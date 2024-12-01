from typing import Callable

from pydantic import (
    AliasChoices,
    BaseModel,
    Field,
    ImportString,
)
from pydantic_settings import BaseSettings, SettingsConfigDict, YamlConfigSettingsSource

from .msg import FrameStamped, WindowInfo
from .windows_capture import construct_pipeline


def callback_sink(*args, **kwargs):
    """A dummy callback function that does nothing"""


class WindowsCaptureArgs(BaseModel):
    on_frame_arrived: ImportString[Callable[[FrameStamped], None]] = Field(
        callback_sink
    )  # Callback function for when a frame arrives
    pipeline_description: str = Field(default_factory=construct_pipeline)  # Optional pipeline description


class WindowPublishArgs(BaseModel):
    # Callback function for when a window is published
    callback: ImportString[Callable[[WindowInfo], None]] = Field(callback_sink)


class ControlPublishArgs(BaseModel):
    keyboard_callback: ImportString = Field(callback_sink)
    mouse_callback: ImportString = Field(callback_sink)


class DesktopArgs(BaseSettings):
    windows_capture_args: WindowsCaptureArgs = Field(default_factory=WindowsCaptureArgs)
    window_publisher_args: WindowPublishArgs = Field(default_factory=WindowPublishArgs)
    control_publisher_args: ControlPublishArgs = Field(default_factory=ControlPublishArgs)
