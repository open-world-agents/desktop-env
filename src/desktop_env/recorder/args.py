from typing import Optional

from ..args import BaseArgs


class RecorderArgs(BaseArgs):
    filesink_location: str
    record_audio: bool = True
    record_video: bool = True
    record_timestamp: bool = True
    enable_appsink: bool = False
    enable_fpsdisplaysink: bool = True

    window_name: Optional[str] = None
    monitor_idx: Optional[int] = None
