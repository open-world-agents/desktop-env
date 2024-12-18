"""ZType game agent that uses a Vision Language Model (VLM) to detect and type words.
This script performs screen capture and simulates keyboard input to automatically play the typing game."""

import threading
import time
from queue import Empty, Full, Queue

import cv2
from loguru import logger
from openai import OpenAI
from PIL import Image
from tqdm import tqdm

from desktop_env import Desktop, DesktopArgs
from desktop_env.msg import FrameStamped
from desktop_env.threading import AbstractThread
from desktop_env.utils import char_to_vk, when_active
from desktop_env.windows_capture import construct_pipeline
from utils import Rate, from_image_to_b64

# Configure loguru with tqdm to handle progress bars and logging together.
logger.remove()
logger.add(lambda msg: tqdm.write(msg, end=""), colorize=True)

# Set DEBUG to True for additional debug information
DEBUG = False  # set to True for debugging

# Name of the window where the ZType game is running
ZTYPE_WINDOW_NAME = "ZType – Typing Game"  # Adjust based on the actual window title

# Shared queue between the agent and actor for passing detected words
MAX_QUEUE_SIZE = 3
word_queue = Queue(maxsize=MAX_QUEUE_SIZE)

# Queue for frame processing - only keeps the latest frame to avoid lag
frame_queue = Queue(maxsize=1)
frame_lock = threading.Lock()  # Thread lock for frame queue access


def on_frame_arrived(frame: FrameStamped):
    """Callback when a new frame arrives from the screen capture."""
    with frame_lock:
        if frame_queue.full():
            frame_queue.get()  # Remove the oldest frame if queue is full
        frame_queue.put(frame)  # Add the new frame to the queue


class ZTypeAgent(AbstractThread):
    """Agent that uses a Vision Language Model to detect words from game screen captures."""

    def __init__(self):
        # Initialize the Vision Language Model (VLM)
        self.model = "OpenGVLab/InternVL2_5-1B"
        self.client = OpenAI(
            api_key="YOUR_API_KEY",  # API key is not required for local models
            base_url="http://localhost:23333/v1",
        )
        # System prompt for the VLM to focus on relevant words in the game
        self.system_prompt = """In this typing game, you type the words that appear on screen to intercept them.
If there is a word highlighted alone in orange, prioritize reading that word exactly as it appears.
If else, among the visible words on screen, tell me the one that appears furthest down (it could be a single letter).
Although letters may overlap, focus only on the word that appears in the foremost layer.
{last_word_instruction}
IMPORTANT: Don't add any additional explanation - just respond with the word positioned lowest on screen"""

        self.stop_event = threading.Event()
        self.last_word = None  # Stores the last word detected to avoid repeats

    def process_frame(self, frame: FrameStamped):
        """Process a single frame through the VLM to detect words."""

        # Save the frame for debugging purposes if DEBUG is True
        if DEBUG:
            frame_rgb = cv2.cvtColor(frame.frame_arr, cv2.COLOR_BGRA2RGB)
            debug_image = Image.fromarray(frame_rgb)
            debug_image.save("debug_frame.png")
            logger.debug("Saved debug frame to debug_frame.png")  # Adjusted to debug level

        # Convert frame to RGB PIL image and resize it for the VLM
        frame_rgb = cv2.cvtColor(frame.frame_arr, cv2.COLOR_BGRA2RGB)
        pil_image = Image.fromarray(frame_rgb)
        pil_image = pil_image.resize((448, 448))  # Resizing as required by the VLM
        base64_image = from_image_to_b64(pil_image).decode("utf-8")

        # Add instruction to ignore the last word detected, if any
        last_word_instruction = ""
        if self.last_word:
            last_word_instruction = f'Ignore the word "{self.last_word}" if you see it.'

        # Format the current prompt for the VLM with the last word instruction
        current_prompt = self.system_prompt.format(last_word_instruction=last_word_instruction)

        # Send the image and prompt to the VLM and receive a response
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": current_prompt},
                            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_image}"}},
                        ],
                    }
                ],
                max_tokens=20,  # Limit response length as only the word is needed
                stream=False,
            )

            logger.debug(f"Raw VLM response: {response}")  # Adjusted to debug level

            # Extract the word from the VLM response
            if response.choices and response.choices[0].message.content:
                word = response.choices[0].message.content.strip()
                if word != self.last_word:  # Process only if it's a new word
                    logger.info(f"Detected word: {word}")
                    try:
                        word_queue.put_nowait((time.time(), word))
                        self.last_word = word  # Update last_word with the new word
                    except Full:
                        logger.warning("Word queue is full, skipping new word")
                else:
                    logger.debug(f"Skipping repeated word: {word}")
            else:
                logger.warning("No word detected in response")
        except Exception as e:
            logger.error(f"Error processing frame with Vision API: {e}")
            logger.exception("Vision API processing error details:")

    def start(self):
        """Main loop for processing frames."""
        rate = Rate(rate=1.0)  # Rate limiter to process frames at 1 FPS
        while not self.stop_event.is_set():
            try:
                with frame_lock:
                    frame = frame_queue.get(timeout=0.1)
                self.process_frame(frame)
                rate.sleep()
            except Empty:
                continue  # No frame available, continue looping

    def start_free_threaded(self):
        """Starts the agent in a separate thread."""
        self._loop_thread = threading.Thread(target=self.start)
        self._loop_thread.start()

    def stop(self):
        """Signals the agent to stop processing frames."""
        self.stop_event.set()


class ZtypeActor(AbstractThread):
    """Actor that types detected words using virtual keyboard inputs."""

    def __init__(self, desktop: Desktop):
        self.stop_event = threading.Event()
        self.desktop = desktop  # Reference to the desktop environment for keyboard control
        self.word_timeout = 2.0  # Ignore words older than 2 seconds

    @when_active(ZTYPE_WINDOW_NAME)
    def type_word(self, word: str):
        """Type a word character by character with natural delays."""
        logger.info(f"Typing word: {word}")  # Adjusted to info level
        for char in word.lower():
            try:
                vk = char_to_vk(char)
                # Simulate natural typing with small delays between key presses
                self.desktop.keyboard.press(vk)
                time.sleep(0.05)  # Delay between key press and release
                self.desktop.keyboard.release(vk)
                time.sleep(0.05)  # Delay between characters
            except Exception as e:
                logger.warning(f"Error typing character '{char}': {e}")

    def start(self):
        """Main loop for receiving words from the queue and typing them."""
        while not self.stop_event.is_set():
            try:
                timestamp, word = word_queue.get(timeout=1)
                # Ignore words that have been in the queue longer than word_timeout
                if time.time() - timestamp > self.word_timeout:
                    logger.info(f"Skipping old word: {word}")  # Adjusted to info level
                    continue
                self.type_word(word)
            except Empty:
                continue  # No word available, continue looping

    def start_free_threaded(self):
        """Starts the actor in a separate thread."""
        self._loop_thread = threading.Thread(target=self.start)
        self._loop_thread.start()

    def stop(self):
        """Signals the actor to stop typing words."""
        self.stop_event.set()


if __name__ == "__main__":
    # Configure desktop environment arguments
    args = DesktopArgs(
        windows_capture_args={
            "on_frame_arrived": on_frame_arrived,
            "pipeline_description": construct_pipeline(
                window_name=ZTYPE_WINDOW_NAME,
                framerate="1/1",  # Reduce framerate to avoid overwhelming the VLM
            ),
        },
        window_publisher_args={"callback": "desktop_env.args.callback_sink"},
        control_publisher_args={
            "keyboard_callback": "desktop_env.args.callback_sink",
            "mouse_callback": "desktop_env.args.callback_sink",
        },
    )
    # Initialize the Desktop environment
    desktop = Desktop.from_args(args)
    # Initialize the ZTypeAgent
    agent = ZTypeAgent()
    # Initialize the ZtypeActor with the desktop reference
    actor = ZtypeActor(desktop=desktop)

    try:
        # Start the desktop and actor in separate threads
        desktop.start_free_threaded()
        actor.start_free_threaded()
        # Run the agent in the main thread for better error handling
        agent.start()
    except KeyboardInterrupt:
        # Handle keyboard interrupt to gracefully shut down
        pass
    finally:
        # Ensure clean shutdown of all components.
        actor.stop_join_close()
        agent.stop_join_close()
        desktop.stop_join_close()
