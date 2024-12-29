import sys
from typing import Type, Union

if sys.platform == 'win32':
    from .windows import WindowsCapture as PlatformCapture
    from .windows import WindowsControl as PlatformControl
    from .windows import WindowsWindow as PlatformWindow
elif sys.platform == 'darwin':
    from .macos import MacOSCapture as PlatformCapture
    from .macos import MacOSControl as PlatformControl
    from .macos import MacOSWindow as PlatformWindow
else:
    raise NotImplementedError(f"Platform {sys.platform} is not supported yet")

__all__ = ['PlatformCapture', 'PlatformControl', 'PlatformWindow']