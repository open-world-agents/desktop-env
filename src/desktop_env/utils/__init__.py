import numpy as np
from pynput.keyboard import Key, KeyCode

from ..window_publisher.utils import get_window_by_title, when_active


def frame_byte_to_np(frame: bytes, *, width: int = 1920, height: int = 1080):
    """Converts video/x-raw,format=BGRA into numpy array."""
    # Extract width and height from the frame data
    frame = np.frombuffer(frame, dtype=np.uint8).reshape((height, width, 4))
    return frame


def key_to_vk(key: Key | KeyCode | None) -> int:
    """Converts a key to a virtual key code.

    The key parameter passed to callbacks is a pynput.keyboard.Key, for special keys, a pynput.keyboard.KeyCode for normal alphanumeric keys, or just None for unknown keys.
    Ref: https://pynput.readthedocs.io/en/latest/keyboard.html#monitoring-the-keyboard
    """
    vk = getattr(key, "vk", None)  # Key, special keys
    if vk is None:
        vk = getattr(key, "value", None).vk  # KeyCode, alphanumeric keys
    return vk


def char_to_vk(char: str) -> int:
    """Converts a character to a virtual key code."""
    if char.isalpha():
        return ord(char.upper())
    elif char.isdigit():
        return ord(char)
    else:
        raise ValueError(f"Unsupported character: {char}")
