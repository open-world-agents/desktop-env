import numpy as np
import pygetwindow as gw

from .msg import WindowInfo


def get_window_by_title(window_title_substring: str) -> WindowInfo:
    windows = gw.getWindowsWithTitle(window_title_substring)
    if windows:
        window: gw.Win32Window = windows[0]
        rect = window._getWindowRect()
        to_send = {
            "title": window.title,
            "rect": (rect.left, rect.top, rect.right, rect.bottom),
            "hWnd": window._hWnd,
        }
        return WindowInfo(**to_send)
    else:
        raise ValueError(f"No window with title containing '{window_title_substring}' found.")


def frame_byte_to_np(frame: bytes, *, width: int = 1920, height: int = 1080):
    """Converts video/x-raw,format=BGRA into numpy array."""
    # Extract width and height from the frame data
    frame = np.frombuffer(frame, dtype=np.uint8).reshape((height, width, 4))
    return frame
