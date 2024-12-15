import pynput
from loguru import logger

from ..utils import key_to_vk
from .msg import KeyboardEvent, MouseEvent


class KeyboardListenerFactory:
    def __init__(self, callback):
        self.callback = callback

    @property
    def listeners(self):
        return {"on_press": self.on_press, "on_release": self.on_release}

    def on_press(self, key):
        vk = key_to_vk(key)
        logger.debug(f"Key {key}({vk}) pressed")  # enum Key / pynput.keyboara._win32.KeyCode
        # logger.debug(
        #     f"{getattr(key, 'vk', None)} {getattr(key, 'char', None)} {getattr(key, 'name', None)} {getattr(key, 'value', None)}"
        # )
        # 82 r None None
        # 67  None None
        # None None ctrl_l <162>
        self.callback(KeyboardEvent(event_type="on_press", event_data=vk))

    def on_release(self, key):
        vk = key_to_vk(key)
        logger.debug(f"Key {key}({vk}) pressed")
        self.callback(KeyboardEvent(event_type="on_release", event_data=vk))


class MouseListenerFactory:
    def __init__(self, callback):
        self.callback = callback

    @property
    def listeners(self):
        return {"on_move": self.on_move, "on_click": self.on_click, "on_scroll": self.on_scroll}

    def on_move(self, x, y):
        logger.trace(f"Mouse moved to ({x}, {y})")
        self.callback(MouseEvent(event_type="on_move", event_data=(x, y)))

    def on_click(self, x, y, button: pynput.mouse.Button, pressed):
        logger.debug(f"Mouse {'pressed' if pressed else 'released'} at ({x}, {y}) with {button.name}")
        self.callback(MouseEvent(event_type="on_click", event_data=(x, y, button.name, pressed)))

    def on_scroll(self, x, y, dx, dy):
        logger.debug(f"Mouse scrolled at ({x}, {y}) with ({dx}, {dy})")
        self.callback(MouseEvent(event_type="on_scroll", event_data=(x, y, dx, dy)))
