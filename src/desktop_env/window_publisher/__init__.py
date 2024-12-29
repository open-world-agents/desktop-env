import threading
import time
import platform
from typing import Callable

from loguru import logger
from tqdm import tqdm

from ..threading import AbstractThread
from .args import WindowPublishArgs
from .msg import WindowInfo


class WindowPublisher(AbstractThread):
    """Publishes the active window information to the callback function every 1/FPS seconds"""

    FPS = 4

    def __init__(self, callback: Callable, verbose: bool):
        self.pbar = tqdm(total=None, desc="Publishing windows info", dynamic_ncols=True, disable=not verbose)
        self.stop_event = threading.Event()
        self.callback = callback
        
        if platform.system() == "Darwin":
            from Quartz import (
                CGWindowListCopyWindowInfo,
                kCGWindowListOptionOnScreenOnly,
                kCGNullWindowID
            )
            self._get_window_info = self._get_window_info_macos
        elif platform.system() == "Windows":
            import pygetwindow as gw
            self.gw = gw
            self._get_window_info = self._get_window_info_windows
        else:
            raise NotImplementedError(f"Platform {platform.system()} is not supported yet")

    def _get_window_info_macos(self):
        from Quartz import (
            CGWindowListCopyWindowInfo,
            kCGWindowListOptionOnScreenOnly,
            kCGNullWindowID
        )
        windows = CGWindowListCopyWindowInfo(kCGWindowListOptionOnScreenOnly, kCGNullWindowID)
        # Get the frontmost window
        for window in windows:
            if window.get('kCGWindowLayer', 0) == 0:  # 0 means frontmost
                bounds = window.get('kCGWindowBounds')
                return WindowInfo(
                    title=window.get('kCGWindowName', ''),
                    rect=(
                        int(bounds['X']),
                        int(bounds['Y']),
                        int(bounds['X'] + bounds['Width']),
                        int(bounds['Y'] + bounds['Height'])
                    ),
                    hWnd=window.get('kCGWindowNumber', 0)
                )
        return None

    def _get_window_info_windows(self):
        active_window = self.gw.getActiveWindow()
        if active_window is not None:
            rect = active_window._getWindowRect()
            return WindowInfo(
                title=active_window.title,
                rect=(rect.left, rect.top, rect.right, rect.bottom),
                hWnd=active_window._hWnd
            )
        return None

    @classmethod
    def from_args(cls, args: WindowPublishArgs):
        return cls(args.callback, args.verbose)

    def start(self):
        while not self.stop_event.is_set():
            window_info = self._get_window_info()
            if window_info is not None:
                self.pbar.update(1)
                self.pbar.set_postfix(title=window_info.title)
                self.callback(window_info)
            time.sleep(1 / self.FPS)

    def start_free_threaded(self):
        self._loop_thread = threading.Thread(target=self.start)
        self._loop_thread.start()

    def stop(self):
        self.stop_event.set()

    def join(self):
        if hasattr(self, "_loop_thread"):
            self._loop_thread.join()

    def close(self): ...
