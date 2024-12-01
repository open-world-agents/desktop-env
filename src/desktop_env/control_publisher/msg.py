import datetime
import time
from typing import Any, Literal

from pydantic import BaseModel, Field


class BaseEvent(BaseModel):
    event_type: str | None = None
    event_data: Any = None
    event_time: int = Field(default_factory=lambda: time.time_ns())  # nanosecond unit in general
    device_name: str | None = None

    def __repr__(self):
        # return f"{self.event_time},{self.event_type},{self.event_data}"
        return f"{datetime.datetime.fromtimestamp(self.event_time / 1e9).strftime('%Y-%m-%d %H:%M:%S')},{self.event_type},{self.event_data}"

    def __lt__(self, other):
        if isinstance(other, BaseEvent):
            return self.event_time < other.event_time
        elif isinstance(other, float) or isinstance(other, int):
            return self.event_time < other
        raise NotImplementedError

    def __gt__(self, other):
        if isinstance(other, BaseEvent):
            return self.event_time > other.event_time
        elif isinstance(other, float) or isinstance(other, int):
            return self.event_time > other
        raise NotImplementedError

    @property
    def event_full_type(self):
        return f"{self.device_name}.{self.event_type}"

    def replay(self):
        raise NotImplementedError


class KeyboardEvent(BaseEvent):
    event_type: Literal["on_press", "on_release"]
    event_data: int  # vk
    device_name: str = "keyboard"

    def replay(self):
        import pynput

        self.__class__.controller = getattr(self.__class__, "controller", pynput.keyboard.Controller())
        controller = self.__class__.controller
        if self.event_type == "on_press":
            key = pynput.keyboard.KeyCode.from_vk(self.event_data)
            controller.press(key)
        elif self.event_type == "on_release":
            key = pynput.keyboard.KeyCode.from_vk(self.event_data)
            controller.release(key)


class MouseEvent(BaseEvent):
    event_type: Literal["on_move", "on_click", "on_scroll"]
    event_data: Any
    device_name: str = "mouse"

    def replay(self):
        import pynput

        self.__class__.controller = getattr(self.__class__, "controller", pynput.mouse.Controller())
        controller = self.__class__.controller
        if self.event_type == "on_move":
            x, y = self.event_data
            controller.position = (x, y)
        elif self.event_type == "on_click":
            x, y, button, pressed = self.event_data
            button = getattr(pynput.mouse.Button, button)
            if pressed:
                controller.press(button)
            else:
                controller.release(button)
        elif self.event_type == "on_scroll":
            x, y, dx, dy = self.event_data
            controller.scroll(dx, dy)
