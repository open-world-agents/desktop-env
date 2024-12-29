from typing import Optional, Callable, Dict, Any
import time
from Quartz import (
    CGEventCreateKeyboardEvent,
    CGEventCreateMouseEvent,
    CGEventPost,
    kCGEventKeyDown,
    kCGEventKeyUp,
    kCGEventLeftMouseDown,
    kCGEventLeftMouseUp,
    kCGEventRightMouseDown,
    kCGEventRightMouseUp,
    kCGEventMouseMoved,
    kCGHIDEventTap,
    CGEventGetLocation,
)
from pynput import keyboard, mouse
from ...control_publisher.msg import Event, EventType

class MacOSControl:
    def __init__(
        self,
        keyboard_callback: Optional[Callable[[Event], None]] = None,
        mouse_callback: Optional[Callable[[Event], None]] = None,
    ):
        self.keyboard_callback = keyboard_callback
        self.mouse_callback = mouse_callback
        self._keyboard_listener = None
        self._mouse_listener = None
        self._key_map = self._create_key_map()
    
    def _create_key_map(self) -> Dict[str, int]:
        # This is a simplified key map. In a real implementation,
        # you would need to map all possible keys to their virtual key codes
        key_map = {}
        for i in range(26):  # A-Z
            key_map[chr(65 + i)] = 0x00 + i
        for i in range(10):  # 0-9
            key_map[str(i)] = 0x1D + i
        return key_map
    
    def _on_key_press(self, key):
        if self.keyboard_callback:
            try:
                key_char = key.char if hasattr(key, 'char') else key.name
                self.keyboard_callback(Event(
                    type=EventType.KEY_DOWN,
                    data={'key': key_char},
                    time=time.time(),
                    device='keyboard'
                ))
            except AttributeError:
                pass
    
    def _on_key_release(self, key):
        if self.keyboard_callback:
            try:
                key_char = key.char if hasattr(key, 'char') else key.name
                self.keyboard_callback(Event(
                    type=EventType.KEY_UP,
                    data={'key': key_char},
                    time=time.time(),
                    device='keyboard'
                ))
            except AttributeError:
                pass
    
    def _on_mouse_move(self, x, y):
        if self.mouse_callback:
            self.mouse_callback(Event(
                type=EventType.MOUSE_MOVE,
                data={'x': x, 'y': y},
                time=time.time(),
                device='mouse'
            ))
    
    def _on_mouse_click(self, x, y, button, pressed):
        if self.mouse_callback:
            event_type = EventType.MOUSE_DOWN if pressed else EventType.MOUSE_UP
            self.mouse_callback(Event(
                type=event_type,
                data={'x': x, 'y': y, 'button': str(button)},
                time=time.time(),
                device='mouse'
            ))
    
    def start(self):
        if self.keyboard_callback:
            self._keyboard_listener = keyboard.Listener(
                on_press=self._on_key_press,
                on_release=self._on_key_release
            )
            self._keyboard_listener.start()
        
        if self.mouse_callback:
            self._mouse_listener = mouse.Listener(
                on_move=self._on_mouse_move,
                on_click=self._on_mouse_click
            )
            self._mouse_listener.start()
    
    def stop(self):
        if self._keyboard_listener:
            self._keyboard_listener.stop()
        if self._mouse_listener:
            self._mouse_listener.stop()
    
    def simulate_key_press(self, key: str):
        key_code = self._key_map.get(key.upper())
        if key_code is not None:
            event = CGEventCreateKeyboardEvent(None, key_code, True)
            CGEventPost(kCGHIDEventTap, event)
    
    def simulate_key_release(self, key: str):
        key_code = self._key_map.get(key.upper())
        if key_code is not None:
            event = CGEventCreateKeyboardEvent(None, key_code, False)
            CGEventPost(kCGHIDEventTap, event)
    
    def simulate_mouse_move(self, x: int, y: int):
        event = CGEventCreateMouseEvent(None, kCGEventMouseMoved, (x, y), 0)
        CGEventPost(kCGHIDEventTap, event)
    
    def simulate_mouse_click(self, x: int, y: int, button: str = 'left'):
        if button == 'left':
            down_type = kCGEventLeftMouseDown
            up_type = kCGEventLeftMouseUp
        else:  # right
            down_type = kCGEventRightMouseDown
            up_type = kCGEventRightMouseUp
        
        down_event = CGEventCreateMouseEvent(None, down_type, (x, y), 0)
        up_event = CGEventCreateMouseEvent(None, up_type, (x, y), 0)
        
        CGEventPost(kCGHIDEventTap, down_event)
        time.sleep(0.1)  # Small delay between down and up
        CGEventPost(kCGHIDEventTap, up_event)