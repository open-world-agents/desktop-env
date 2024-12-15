import threading
import time
from typing import Callable

import pygetwindow as gw
from loguru import logger
from tqdm import tqdm

from ..threading import AbstractThread
from .args import WindowPublishArgs
from .msg import WindowInfo


class WindowPublisher(AbstractThread):
    """Publishes the active window information to the callback function every 1/FPS seconds"""

    FPS = 4

    def __init__(self, callback: Callable):
        self.pbar = tqdm(total=None, desc="Publishing windows info", dynamic_ncols=True)
        self.stop_event = threading.Event()
        self.callback = callback

    @classmethod
    def from_args(cls, args: WindowPublishArgs):
        return cls(args.callback)

    def start(self):
        while not self.stop_event.is_set():
            active_window = gw.getActiveWindow()
            if active_window is not None:
                rect = active_window._getWindowRect()
                to_send = {
                    "title": active_window.title,
                    "rect": (rect.left, rect.top, rect.right, rect.bottom),
                    "hWnd": active_window._hWnd,
                }
                self.pbar.update(1)
                self.pbar.set_postfix(**to_send)
                self.callback(WindowInfo(**to_send))
                time.sleep(1 / self.FPS)
            else:
                logger.warning("No active window found.")

    def start_free_threaded(self):
        self._loop_thread = threading.Thread(target=self.start)
        self._loop_thread.start()

    def stop(self):
        self.stop_event.set()

    def join(self):
        if hasattr(self, "_loop_thread"):
            self._loop_thread.join()

    def close(self): ...
