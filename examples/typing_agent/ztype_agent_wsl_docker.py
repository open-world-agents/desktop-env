"""ZType game agent that uses Vision Language Model to detect and type words.
Uses screen capture and keyboard simulation to play the typing game automatically."""

import threading
import time
from queue import Empty, Full, Queue

import cv2
from loguru import logger
from PIL import Image

from openai import OpenAI

from desktop_env import Desktop, DesktopArgs
from desktop_env.msg import FrameStamped
from desktop_env.threading import AbstractThread
from desktop_env.utils import char_to_vk, when_active
from desktop_env.windows_capture import construct_pipeline

DEBUG = False # set to True for debugging
ZTYPE_WINDOW_NAME = "ZType – Typing Game"  # ZType – Typing Game - Type to Shoot - Chrome

# Shared queue between agent and actor for passing detected words
MAX_QUEUE_SIZE = 3
word_queue = Queue(maxsize=MAX_QUEUE_SIZE)


class ZTypeAgent(AbstractThread):
    """Agent that uses VLM to detect words from game screen captures."""
    
    def __init__(self):
        # Initialize VLM model
        self.model = "OpenGVLab/InternVL2_5-1B"
        self.client = OpenAI(
            api_key="YOUR_API_KEY", # Since API key is not required here, it's fine as is.
            base_url="http://localhost:23333/v1"
        )
        # Prompt engineering to make VLM focus on the most relevant word
        self.system_prompt = """In this typing game, you type the words that appear on screen to intercept them.
If there is a word highlighted alone in orange, prioritize reading that word exactly as it appears.
If else, among the visible words on screen, tell me the one that appears furthest down (it could be a single letter).
Although letters may overlap, focus only on the word that appears in the foremost layer.
{last_word_instruction}
IMPORTANT: Don't add any additional explanation - just respond with the word positioned lowest on screen"""

        # Queue for frame processing - only keeps latest frame to avoid lag
        self.frame_queue = Queue(maxsize=1)  # Only keep latest frame
        self.frame_lock = threading.Lock()  # To ensure thread safety

        self.stop_event = threading.Event()
        self.is_processing = threading.Event()  # check if currently processing
        self.last_word = None  # last word detected

    def on_frame_arrived(self, frame: FrameStamped):
        """Callback for new frames - updates frame queue with latest frame only."""
        with self.frame_lock:
            if self.frame_queue.full():
                self.frame_queue.get()
            self.frame_queue.put(frame)

    def process_frame(self, frame: FrameStamped):
        """Process a single frame through VLM to detect words."""
        # if currently processing, skip new frame
        if self.is_processing.is_set():
            logger.debug("Skipping frame - currently processing")
            return

        self.is_processing.set()
        try:
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
            # resize image to 448x448
            pil_image = pil_image.resize((448, 448))
            logger.info("Converted frame to PIL Image")

            # Save image to bytes
            import io
            img_byte_arr = io.BytesIO()
            pil_image.save(img_byte_arr, format="PNG")
            img_byte_arr = img_byte_arr.getvalue()

            # Encode image to base64
            import base64
            base64_image = base64.b64encode(img_byte_arr).decode("utf-8")

            time.sleep(1)

            # Add instruction to ignore last word if it's detected
            last_word_instruction = ""
            if self.last_word:
                last_word_instruction = f'Ignore the word "{self.last_word}" if you see it.'
            
            current_prompt = self.system_prompt.format(
                last_word_instruction=last_word_instruction
            )

            # Process with VLM and extract detected word
            logger.info("Sending frame to VLM...")
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": current_prompt
                                },
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/png;base64,{base64_image}"
                                    }
                                }
                            ]
                        }
                    ],
                    max_tokens=20,  # Keep response short since we only need the word
                    stream=False
                )

                logger.info(f"Raw VLM response: {response}")
                
                if response.choices and response.choices[0].message.content:
                    word = response.choices[0].message.content.strip()
                    if word != self.last_word:  # 마지막 단어와 다른 경우에만 처리
                        logger.info(f"Detected word: {word}")
                        try:
                            word_queue.put_nowait((time.time(), word))
                            self.last_word = word  # 새로운 단어를 마지막 단어로 저장
                        except Full:
                            logger.warning("Word queue is full, skipping new word")
                    else:
                        logger.debug(f"Skipping repeated word: {word}")
                else:
                    logger.warning("No word detected in response")
            except Exception as e:
                logger.error(f"Error processing frame with Vision API: {e}")
                logger.exception("Vision API processing error details:")
                time.sleep(1)
        finally:
            self.is_processing.clear()

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
        self.word_timeout = 2.0  # 2초 이상 된 단어는 무시

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
                timestamp, word = word_queue.get(timeout=1)
                # ignore old words
                if time.time() - timestamp > self.word_timeout:
                    logger.warning(f"Skipping old word: {word}")
                    continue
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
