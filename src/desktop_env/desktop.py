import time

from .actor import ActorMixin
from .args import DesktopArgs
from .control_publisher import ControlPublisher
from .threading import AbstractThread
from .window_publisher import WindowPublisher
from .windows_capture import WindowsCapture


class Desktop(AbstractThread, ActorMixin):
    def __init__(self, args: DesktopArgs):
        super().__init__()

        # Create threads
        self.threads = []

        windows_capture = WindowsCapture(**args.windows_capture_args.model_dump())
        self.threads.append(windows_capture)

        window_publisher = WindowPublisher(args.window_publisher_args.callback)
        self.threads.append(window_publisher)

        control_publisher = ControlPublisher(
            args.control_publisher_args.keyboard_callback, args.control_publisher_args.mouse_callback
        )
        self.threads.append(control_publisher)

    @classmethod
    def from_settings(cls, settings: DesktopArgs):
        return cls(settings)

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
