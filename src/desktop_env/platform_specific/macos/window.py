from typing import Optional, Callable, Tuple
import time
from Quartz import (
    CGWindowListCopyWindowInfo,
    kCGWindowListOptionOnScreenOnly,
    kCGNullWindowID,
    CGWindowListCreateImage,
    CGRectNull,
)
from ...window_publisher.msg import Event, EventType

class MacOSWindow:
    def __init__(
        self,
        callback: Optional[Callable[[Event], None]] = None,
    ):
        self.callback = callback
        self.running = False
        self._last_active_window = None
    
    def _get_active_window(self) -> Tuple[Optional[str], Optional[Tuple[int, int, int, int]], Optional[int]]:
        window_list = CGWindowListCopyWindowInfo(kCGWindowListOptionOnScreenOnly, kCGNullWindowID)
        for window in window_list:
            # In macOS, the frontmost window is typically the first one in the list
            if window.get("kCGWindowLayer", 0) == 0:  # Main window layer
                name = window.get("kCGWindowName", "")
                bounds = window.get("kCGWindowBounds", {})
                window_id = window.get("kCGWindowNumber")
                
                if bounds:
                    x = int(bounds.get("X", 0))
                    y = int(bounds.get("Y", 0))
                    width = int(bounds.get("Width", 0))
                    height = int(bounds.get("Height", 0))
                    rect = (x, y, width, height)
                else:
                    rect = None
                
                return name, rect, window_id
        
        return None, None, None
    
    def start(self):
        self.running = True
        
        while self.running:
            title, rect, window_id = self._get_active_window()
            
            if title != self._last_active_window:
                self._last_active_window = title
                if self.callback:
                    self.callback(Event(
                        type=EventType.WINDOW_FOCUS,
                        title=title,
                        rect=rect,
                        hWnd=window_id,
                        time=time.time()
                    ))
            
            time.sleep(0.1)  # Check every 100ms
    
    def stop(self):
        self.running = False