import platform
import pygetwindow as gw

from .msg import WindowInfo


def get_window_by_title(window_title_substring: str) -> WindowInfo:
    windows = gw.getWindowsWithTitle(window_title_substring)
    if not windows:
        raise ValueError(f"No window with title containing '{window_title_substring}' found.")
        
    window = windows[0]
    os_name = platform.system()
    
    if os_name == "Windows":
        rect = window._getWindowRect()
        to_send = {
            "title": window.title,
            "rect": (rect.left, rect.top, rect.right, rect.bottom),
            "hWnd": window._hWnd,
        }
    elif os_name == "Darwin":
        # Mac OS uses different window attributes
        to_send = {
            "title": window.title,
            "rect": (window.left, window.top, window.right, window.bottom),
            "hWnd": window._hWnd if hasattr(window, '_hWnd') else 0,  # Mac doesn't use hWnd
        }
    else:
        # Linux or other OS
        to_send = {
            "title": window.title,
            "rect": (window.left, window.top, window.right, window.bottom),
            "hWnd": 0,
        }
    
    return WindowInfo(**to_send)


def when_active(window_title_substring: str):
    """Decorator to run the function when the window with the title containing the substring is active."""

    def decorator(func):
        def wrapper(*args, **kwargs):
            window = get_window_by_title(window_title_substring)
            if gw.getActiveWindow()._hWnd == window.hWnd:
                return func(*args, **kwargs)

        return wrapper

    return decorator
