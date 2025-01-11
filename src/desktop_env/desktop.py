import importlib
import time

from .actor import ActorMixin
from .desktop_args import DesktopArgs
from .threading import AbstractThread


class Desktop(AbstractThread, ActorMixin):
    def __init__(self, args: DesktopArgs):
        super().__init__()

        # Create threads
        self.threads = []

        for submodule in args.submodules:
            if isinstance(submodule, str):
                module: AbstractThread = importlib.import_module(submodule.module)
            else:
                module: AbstractThread = submodule.module
            thread = module.from_args(submodule.args)
            self.threads.append(thread)

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
