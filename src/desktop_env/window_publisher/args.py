from typing import Callable

from pydantic import BaseModel, Field, ImportString

from ..args import BaseArgs, callback_sink
from .msg import WindowInfo


class WindowPublishArgs(BaseArgs):
    # Callback function for when a window is published
    callback: ImportString[Callable[[WindowInfo], None]]
    verbose: bool = Field(False, description="Whether to print debug information")
