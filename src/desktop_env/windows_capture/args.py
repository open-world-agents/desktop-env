from typing import Callable

from pydantic import BaseModel, Field, ImportString

from ..args import BaseArgs, callback_sink
from .gst_pipeline import construct_pipeline
from .msg import FrameStamped


class WindowsCaptureArgs(BaseArgs):
    on_frame_arrived: ImportString[Callable[[FrameStamped], None]]  # Callback function for when a frame arrives
    pipeline_description: str = Field(default_factory=construct_pipeline)  # Optional pipeline description
