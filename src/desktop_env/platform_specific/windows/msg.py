import numpy as np
from pydantic import BaseModel


class FrameStamped(BaseModel):
    class Config:
        arbitrary_types_allowed = True

    timestamp_ns: int
    frame_arr: np.ndarray  # [W, H, BGRA]
