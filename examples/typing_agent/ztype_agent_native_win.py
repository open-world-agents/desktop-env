"""ZType game agent that uses Vision Language Model to detect and type words.
Uses screen capture and keyboard simulation to play the typing game automatically."""

import threading
import time
from queue import Empty, Full, Queue

import cv2
from lmdeploy import TurbomindEngineConfig, pipeline
from lmdeploy.vl import load_image
from loguru import logger
from PIL import Image

from desktop_env import Desktop, DesktopArgs
from desktop_env.msg import FrameStamped
from desktop_env.threading import AbstractThread
from desktop_env.utils import char_to_vk, when_active
from desktop_env.windows_capture import construct_pipeline

DEBUG = True
ZTYPE_WINDOW_NAME = "ZType – Typing Game"  # ZType – Typing Game - Type to Shoot - Chrome

# Shared queue between agent and actor for passing detected words
word_queue = Queue()


class ZTypeAgent(AbstractThread):
    """Agent that uses VLM to detect words from game screen captures."""
    
    def __init__(self):
        # Initialize VLM model
        self.model = "OpenGVLab/InternVL2_5-1B"
        self.pipe = pipeline(self.model, backend_config=TurbomindEngineConfig(session_len=8192))
        # Prompt engineering to make VLM focus on the most relevant word
        self.system_prompt = """In this typing game, you type the words that appear on screen to intercept them.
If there is a word highlighted alone in orange, prioritize reading that word exactly as it appears.
If else, among the visible words on screen, tell me the one that appears furthest down (it could be a single letter).
Although letters may overlap, focus only on the word that appears in the foremost layer.
IMPORTANT: Don't add any additional explanation - just respond with the word positioned lowest on screen"""

        # Queue for frame processing - only keeps latest frame to avoid lag
        self.frame_queue = Queue(maxsize=1)  # Only keep latest frame
        self.frame_lock = threading.Lock()  # To ensure thread safety

        self.stop_event = threading.Event()

    def on_frame_arrived(self, frame: FrameStamped):
        """Callback for new frames - updates frame queue with latest frame only."""
        with self.frame_lock:
            if self.frame_queue.full():
                self.frame_queue.get()
            self.frame_queue.put(frame)

    def process_frame(self, frame: FrameStamped):
        """Process a single frame through VLM to detect words."""
        # Save frame for debugging if enabled
        if DEBUG:
            frame_rgb = cv2.cvtColor(frame.frame_arr, cv2.COLOR_BGRA2RGB)
            debug_image = Image.fromarray(frame_rgb)
            debug_image.save("debug_frame.png")
            logger.info("Saved debug frame to debug_frame.png")

        # Log frame info for debugging
        logger.info(f"Processing frame with shape: {frame.frame_arr.shape}")

        # Convert frame to format required by VLM
        frame_rgb = cv2.cvtColor(frame.frame_arr, cv2.COLOR_BGRA2RGB)
        pil_image = Image.fromarray(frame_rgb)
        logger.info("Converted frame to PIL Image")

        # Process with VLM and extract detected word
        logger.info("Sending frame to VLM...")
        try:
            response = self.pipe((self.system_prompt, pil_image))
            logger.info(f"Raw VLM response: {response}")

            if response and isinstance(response.text, str):
                word = response.text.strip()
                logger.info(f"Detected word: {word}")
                # Non-blocking put to avoid deadlocks
                word_queue.put_nowait(word)
            else:
                logger.warning(f"Unexpected response type: {type(response)}")
        except Exception as e:
            logger.error(f"Error processing frame with VLM: {e}")
            logger.exception("VLM processing error details:")

    def start(self):
        while not self.stop_event.is_set():
            try:
                logger.debug("Waiting for frame...")
                with self.frame_lock:
                    frame = self.frame_queue.get(timeout=1)
                logger.info("Got new frame from queue")
                self.process_frame(frame)
            except Empty:
                continue

    def start_free_threaded(self):
        self._loop_thread = threading.Thread(target=self.start)
        self._loop_thread.start()

    def stop(self):
        self.stop_event.set()


class ZtypeActor(AbstractThread):
    """Actor that types detected words using virtual keyboard inputs."""
    
    def __init__(self, desktop: Desktop):
        self.stop_event = threading.Event()
        self.desktop = desktop

    @when_active(ZTYPE_WINDOW_NAME)
    def type_word(self, word: str):
        """Type a word character by character with natural delays."""
        logger.debug(f"Typing word: {word}")
        for char in word.lower():
            try:
                vk = char_to_vk(char)
                # Simulate natural typing with small delays
                self.desktop.keyboard.press(vk)
                time.sleep(0.05)  # Delay between press and release
                self.desktop.keyboard.release(vk)
                time.sleep(0.05)  # Delay between characters
            except Exception as e:
                logger.warning(f"Error typing character '{char}': {e}")

    def start(self):
        while not self.stop_event.is_set():
            try:
                word = word_queue.get(timeout=1)
                self.type_word(word)
            except Empty:
                continue

    def start_free_threaded(self):
        self._loop_thread = threading.Thread(target=self.start)
        self._loop_thread.start()

    def stop(self):
        self.stop_event.set()


if __name__ == "__main__":
    # TODO: Allow unused arguments to be omitted in DesktopArgs
    agent = ZTypeAgent()
    args = DesktopArgs(
        windows_capture_args={
            "on_frame_arrived": agent.on_frame_arrived,
            "pipeline_description": construct_pipeline(
                window_name=ZTYPE_WINDOW_NAME,
                framerate="1/1",  # Reduce framerate to avoid overwhelming VLM
            ),
        },
        window_publisher_args={"callback": "desktop_env.args.callback_sink"},
        control_publisher_args={
            "keyboard_callback": "desktop_env.args.callback_sink",
            "mouse_callback": "desktop_env.args.callback_sink",
        },
    )
    desktop = Desktop.from_args(args)
    actor = ZtypeActor(desktop=desktop)  # TODO: Improve design of actor initialization

    # TODO: add callback post-registration feature
    # desktop.threads[0].on_frame_arrived = agent.on_frame_arrived

    try:
        # Start desktop and actor in separate threads
        desktop.start_free_threaded()
        actor.start_free_threaded()
        # Run agent in main thread for better error handling
        agent.start()
    except KeyboardInterrupt:
        ...
    finally:
        # Ensure clean shutdown of all components
        actor.stop_join_close()
        agent.stop_join_close()
        desktop.stop_join_close()