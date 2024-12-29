import importlib
import time

from .actor import ActorMixin
from .control_publisher import ControlPublisher
from .desktop_args import DesktopArgs
from .threading import AbstractThread
from .window_publisher import WindowPublisher
from .platform_specific import PlatformCapture


class Desktop(AbstractThread, ActorMixin):
    def __init__(self, args: DesktopArgs):
        super().__init__()

        # Create threads
        self.threads = []

        platform_capture = PlatformCapture.from_args(args.windows_capture_args)
        self.threads.append(platform_capture)

        window_publisher = WindowPublisher.from_args(args.window_publisher_args)
        self.threads.append(window_publisher)

        control_publisher = ControlPublisher.from_args(args.control_publisher_args)
        self.threads.append(control_publisher)

    @classmethod
    def from_args(cls, args: DesktopArgs):
        return cls(args)

    def start(self):
        self.start_free_threaded()
        while True:
            time.sleep(1)

    def start_free_threaded(self):
        for thread in self.threads:
            thread.start_free_threaded()

    def stop(self):
        for thread in self.threads:
            thread.stop()

    def join(self):
        for thread in self.threads:
            thread.join()

    def close(self):
        for thread in self.threads:
            thread.close()
