import threading

from .args import BaseArgs


class AbstractThread:
    """Abstract class for creating threads.
    Thread's lifecycle: start -> stop -> join -> close
    """

    args_cls = BaseArgs

    def __init__(self):
        super().__init__()

    @classmethod
    def from_args(cls, args: BaseArgs):
        raise NotImplementedError

    def start(self):
        """Start the task. This function will block the current thread."""

    def start_free_threaded(self):
        """Start the task in a separate thread. This function will not block the current thread."""

    def stop(self): ...
    def join(self): ...
    def close(self): ...

    def stop_join_close(self):
        """Helper function to stop, join, and close the task."""
        self.stop()
        self.join()
        self.close()


class StoppableThread(threading.Thread):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._running = threading.Event()

    def run(self) -> None:
        if self._running.is_set():
            return
        self._running.set()
        while self._running.is_set():
            ...

    def stop(self) -> None:
        self._running.clear()
