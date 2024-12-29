import platform

from .msg import WindowInfo


def get_window_by_title(window_title_substring: str) -> WindowInfo:
    os_name = platform.system()
    if os_name == "Windows":
        import pygetwindow as gw
        windows = gw.getWindowsWithTitle(window_title_substring)
        if not windows:
            raise ValueError(f"No window with title containing '{window_title_substring}' found.")
        window = windows[0]
        rect = window._getWindowRect()
        return WindowInfo(
            title=window.title,
            rect=(rect.left, rect.top, rect.right, rect.bottom),
            hWnd=window._hWnd
        )
    elif os_name == "Darwin":
        from Quartz import (
            CGWindowListCopyWindowInfo,
            kCGWindowListOptionOnScreenOnly,
            kCGNullWindowID,
            kCGWindowLayer
        )
        
        windows = CGWindowListCopyWindowInfo(kCGWindowListOptionOnScreenOnly, kCGNullWindowID)
        for window in windows:
            # Skip windows that are not on normal level (like menu bars, etc)
            if window.get(kCGWindowLayer, 0) != 0:
                continue
                
            # Get window name from either kCGWindowName or kCGWindowOwnerName
            title = window.get('kCGWindowName', '')
            if not title:
                title = window.get('kCGWindowOwnerName', '')
            print(f"title: {title}")
            
            if title and window_title_substring.lower() in title.lower():
                bounds = window.get('kCGWindowBounds')
                if bounds:
                    return WindowInfo(
                        title=title,
                        rect=(
                            int(bounds['X']),
                            int(bounds['Y']),
                            int(bounds['X'] + bounds['Width']),
                            int(bounds['Y'] + bounds['Height'])
                        ),
                        hWnd=window.get('kCGWindowNumber', 0)
                    )
        
        raise ValueError(f"No window with title containing '{window_title_substring}' found.")
    else:
        # Linux or other OS (not implemented yet)
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
            import pygetwindow as gw
            if gw.getActiveWindow()._hWnd == window.hWnd:
                return func(*args, **kwargs)

        return wrapper

    return decorator
