from typing import Optional

from .args import BaseArgs
from .control_publisher.args import ControlPublishArgs
from .window_publisher.args import WindowPublishArgs
from .windows_capture.args import WindowsCaptureArgs


class DesktopArgs(BaseArgs):
    windows_capture_args: Optional[WindowsCaptureArgs] = None
    window_publisher_args: Optional[WindowPublishArgs] = None
    control_publisher_args: Optional[ControlPublishArgs] = None
