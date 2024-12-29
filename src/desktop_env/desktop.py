import importlib
import time

from .actor import ActorMixin
from .control_publisher import ControlPublisher
from .desktop_args import DesktopArgs
from .threading import AbstractThread
from .window_publisher import WindowPublisher
from .windows_capture import WindowsCapture


class Desktop(AbstractThread, ActorMixin):
    def __init__(self, args: DesktopArgs):
        super().__init__()

        # Create threads
        self.threads = []

        windows_capture = WindowsCapture.from_args(args.windows_capture_args)
        self.threads.append(windows_capture)

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
            try:
                thread.start_free_threaded()
            except Exception as e:
                # Catch error and gracefully shutdown
                print(f"Error starting thread {thread}: {e}")
                self.stop_join_close()
                exit(1)

    def stop(self):
        for thread in self.threads:
            thread.stop()

    def join(self):
        for thread in self.threads:
            thread.join()

    def close(self):
        for thread in self.threads:
            thread.close()
