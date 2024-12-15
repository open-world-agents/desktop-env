from typing import Callable

from pydantic import BaseModel, Field, ImportString

from ..args import BaseArgs, callback_sink
from .msg import KeyboardEvent, MouseEvent


class ControlPublishArgs(BaseArgs):
    keyboard_callback: ImportString[Callable[[KeyboardEvent], None]] = Field(callback_sink)
    mouse_callback: ImportString[Callable[[MouseEvent], None]] = Field(callback_sink)
