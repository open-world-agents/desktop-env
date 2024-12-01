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
        key_code = pynput.keyboard.KeyCode.from_vk(key)
        self.controller.press(key_code)

    def release(self, key: int) -> None:
        key_code = pynput.keyboard.KeyCode.from_vk(key)
        self.controller.release(key_code)


class ActorMixin:
    def __init__(self):
        self.mouse = MouseController()
        self.keyboard = KeyboardController()
