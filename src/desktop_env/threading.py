import threading


class AbstractThread:
    """Abstract class for creating threads.
    Thread's lifecycle: start -> stop -> join -> close
    """

    def __init__(self):
        super().__init__()

    def start(self):
        """Start the task. This function will block the current thread."""

    def start_free_threaded(self):
        """Start the task in a separate thread. This function will not block the current thread."""

    def stop(self): ...
    def join(self): ...
    def close(self): ...


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
