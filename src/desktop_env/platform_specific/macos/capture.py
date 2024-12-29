from typing import Optional, Callable
import time
import numpy as np
from Quartz import (
    CGWindowListCopyWindowInfo,
    kCGWindowListOptionOnScreenOnly,
    kCGNullWindowID,
    CGWindowListCreateImage,
    CGRectNull,
    kCGWindowImageDefault,
)
from loguru import logger
from ...msg import FrameStamped

class MacOSCapture:
    def __init__(
        self,
        window_name: Optional[str] = None,
        monitor_idx: Optional[int] = None,
        framerate: str = "60/1",
        on_frame_arrived: Optional[Callable[[FrameStamped], None]] = None,
    ):
        self.window_name = window_name
        self.monitor_idx = monitor_idx
        self.framerate = self._parse_framerate(framerate)
        self.on_frame_arrived = on_frame_arrived
        self.running = False
        self._window_id = None
        
        if window_name:
            self._find_window()
    
    def _parse_framerate(self, framerate: str) -> float:
        num, denom = map(int, framerate.split("/"))
        return num / denom
    
    def _find_window(self):
        window_list = CGWindowListCopyWindowInfo(kCGWindowListOptionOnScreenOnly, kCGNullWindowID)
        for window in window_list:
            name = window.get("kCGWindowName", "")
            if name and self.window_name in name:
                self._window_id = window.get("kCGWindowNumber")
                logger.info(f"Found window: {name} (id: {self._window_id})")
                break
        if not self._window_id:
            raise ValueError(f"Window with name containing '{self.window_name}' not found")
    
    def _capture_frame(self) -> np.ndarray:
        image = CGWindowListCreateImage(
            CGRectNull,  # Capture entire screen
            kCGWindowListOptionOnScreenOnly,
            self._window_id or kCGNullWindowID,
            kCGWindowImageDefault
        )
        if not image:
            return None
        
        width = image.width()
        height = image.height()
        bytes_per_row = image.bytesPerRow()
        pixel_data = image.dataProvider().data().bytes().tobytes()
        
        # Convert to numpy array (BGRA format)
        frame = np.frombuffer(pixel_data, dtype=np.uint8)
        frame = frame.reshape((height, bytes_per_row // 4, 4))
        frame = frame[:, :width]  # Trim any padding
        frame = frame[:, :, [2, 1, 0, 3]]  # Convert BGRA to RGBA
        
        return frame
    
    def start(self):
        self.running = True
        frame_interval = 1.0 / self.framerate
        last_frame_time = 0
        
        while self.running:
            current_time = time.time()
            if current_time - last_frame_time >= frame_interval:
                frame = self._capture_frame()
                if frame is not None and self.on_frame_arrived:
                    self.on_frame_arrived(FrameStamped(
                        frame=frame,
                        timestamp=current_time
                    ))
                last_frame_time = current_time
            else:
                time.sleep(0.001)  # Small sleep to prevent CPU overuse
    
    def stop(self):
        self.running = False