import platform
from typing import Literal

import pynput


class MouseController:
    def __init__(self):
        self.controller = pynput.mouse.Controller()

    def move(self, x: int, y: int):
        self.controller.position = (x, y)

    def click(self, x: int, y: int, button: Literal["left", "right", "middle"], pressed: bool) -> None:
        # TODO: win32 button also contain x1 and x2.
        button = getattr(pynput.mouse.Button, button)
        self.move(x, y)
        if pressed:
            self.controller.press(button)
        else:
            self.controller.release(button)

    def scroll(self, dx: int, dy: int) -> None:
        self.controller.scroll(dx, dy)


class KeyboardController:
    def __init__(self):
        self.controller = pynput.keyboard.Controller()

    def press(self, key: int) -> None:
        if platform.system() == "Darwin":
            # Special key handling for Mac OS
            special_keys = {
                58: pynput.keyboard.Key.alt,      # Option
                55: pynput.keyboard.Key.cmd,      # Command
                59: pynput.keyboard.Key.ctrl,     # Control
                56: pynput.keyboard.Key.shift,    # Shift
                36: pynput.keyboard.Key.enter,    # Return
                49: pynput.keyboard.Key.space,    # Space
                51: pynput.keyboard.Key.backspace,# Delete
                117: pynput.keyboard.Key.delete,  # Forward Delete
                48: pynput.keyboard.Key.tab,      # Tab
                53: pynput.keyboard.Key.esc,      # Escape
            }
            if key in special_keys:
                self.controller.press(special_keys[key])
                return
        key_code = pynput.keyboard.KeyCode.from_vk(key)
        self.controller.press(key_code)

    def release(self, key: int) -> None:
        if platform.system() == "Darwin":
            special_keys = {
                58: pynput.keyboard.Key.alt,      # Option
                55: pynput.keyboard.Key.cmd,      # Command
                59: pynput.keyboard.Key.ctrl,     # Control
                56: pynput.keyboard.Key.shift,    # Shift
                36: pynput.keyboard.Key.enter,    # Return
                49: pynput.keyboard.Key.space,    # Space
                51: pynput.keyboard.Key.backspace,# Delete
                117: pynput.keyboard.Key.delete,  # Forward Delete
                48: pynput.keyboard.Key.tab,      # Tab
                53: pynput.keyboard.Key.esc,      # Escape
            }
            if key in special_keys:
                self.controller.release(special_keys[key])
                return
        key_code = pynput.keyboard.KeyCode.from_vk(key)
        self.controller.release(key_code)


class ActorMixin:
    def __init__(self):
        self.mouse = MouseController()
        self.keyboard = KeyboardController()
