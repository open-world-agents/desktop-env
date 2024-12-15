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


def when_active(window_title_substring: str):
    """Decorator to run the function when the window with the title containing the substring is active."""

    def decorator(func):
        def wrapper(*args, **kwargs):
            window = get_window_by_title(window_title_substring)
            if gw.getActiveWindow()._hWnd == window.hWnd:
                return func(*args, **kwargs)

        return wrapper

    return decorator
