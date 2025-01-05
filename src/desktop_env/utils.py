import platform
from typing import Union

import pynput


def key_to_vk(key: Union[pynput.keyboard.Key, pynput.keyboard._base.KeyCode]) -> int:
    """Convert a pynput key to a virtual key code."""
    os_name = platform.system()

    if os_name == "Windows":
        # Windows uses virtual key codes
        if isinstance(key, pynput.keyboard.Key):
            return key.value.vk
        return key.vk
    elif os_name == "Darwin":
        # Mac OS uses key codes
        if isinstance(key, pynput.keyboard.Key):
            # Map common special keys
            mac_key_map = {
                pynput.keyboard.Key.alt: 58,  # Option key
                pynput.keyboard.Key.alt_l: 58,  # Left Option
                pynput.keyboard.Key.alt_r: 61,  # Right Option
                pynput.keyboard.Key.cmd: 55,  # Command key
                pynput.keyboard.Key.cmd_l: 55,  # Left Command
                pynput.keyboard.Key.cmd_r: 54,  # Right Command
                pynput.keyboard.Key.ctrl: 59,  # Control key
                pynput.keyboard.Key.ctrl_l: 59,  # Left Control
                pynput.keyboard.Key.ctrl_r: 62,  # Right Control
                pynput.keyboard.Key.shift: 56,  # Shift key
                pynput.keyboard.Key.shift_l: 56,  # Left Shift
                pynput.keyboard.Key.shift_r: 60,  # Right Shift
                pynput.keyboard.Key.enter: 36,  # Return
                pynput.keyboard.Key.space: 49,  # Space
                pynput.keyboard.Key.backspace: 51,  # Delete
                pynput.keyboard.Key.delete: 117,  # Forward Delete
                pynput.keyboard.Key.tab: 48,  # Tab
                pynput.keyboard.Key.esc: 53,  # Escape
            }
            return mac_key_map.get(key, 0)
        # For regular keys, use the ASCII value
        return ord(key.char.lower()) if hasattr(key, "char") else 0
    else:
        # For other OS, fallback to ASCII values
        if isinstance(key, pynput.keyboard.Key):
            return key.value.vk if hasattr(key.value, "vk") else 0
        return ord(key.char.lower()) if hasattr(key, "char") else 0
