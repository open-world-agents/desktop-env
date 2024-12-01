import time
from typing import Callable

import pynput
from tqdm import tqdm

from ..threading import AbstractThread
from .callback_factory import KeyboardListenerFactory, MouseListenerFactory


class ControlPublisher(AbstractThread):
    def __init__(self, keyboard_callback: Callable, mouse_callback: Callable):
        self.pbar = tqdm(total=None, desc="Publishing captured control(keyboard/mouse)", dynamic_ncols=True)
        self.keyboard_callback = keyboard_callback
        self.mouse_callback = mouse_callback
        self._listeners = {}

        # Capture keyboard events
        factory = KeyboardListenerFactory(self.keyboard_callback)
        listener = pynput.keyboard.Listener(**factory.listeners)
        self._listeners["keyboard"] = listener

        # Capture mouse events
        factory = MouseListenerFactory(self.mouse_callback)
        listener = pynput.mouse.Listener(**factory.listeners)
        self._listeners["mouse"] = listener

    def start(self):
        self.start_free_threaded()
        while True:
            time.sleep(1)

    def start_free_threaded(self):
        for listener in self._listeners.values():
            listener.start()

    def stop(self):
        for listener in self._listeners.values():
            listener.stop()

    def join(self):
        for listener in self._listeners.values():
            listener.join()

    def close(self): ...
