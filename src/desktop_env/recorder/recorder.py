import os
import subprocess
import threading

from ..threading import AbstractThread
from .args import RecorderArgs
from .gst_pipeline import construct_pipeline


class Recorder(AbstractThread):
    args_cls = RecorderArgs

    def __init__(self, args: RecorderArgs):
        pipeline_description = construct_pipeline(**args.model_dump())
        self._pipeline = f"gst-launch-1.0 -e -v {pipeline_description}"
        self._process = None
        self._loop_thread = None  # Initialize loop thread

    @classmethod
    def from_args(cls, args: RecorderArgs):
        return cls(args)

    def start(self):
        """Start the pipeline. This function will block the current thread."""
        # Prepare the environment variable
        env = os.environ.copy()
        # Set GST_PLUGIN_PATH to the 'custom_plugin' directory in the current working directory
        env["GST_PLUGIN_PATH"] = os.path.join(os.getcwd(), "custom_plugin")
        # Start the process with the modified environment
        self._process = subprocess.Popen(self._pipeline, shell=True, env=env)
        self._process.wait()

    def start_free_threaded(self):
        """Start the pipeline in a separate thread. This function will not block the current thread."""
        self._loop_thread = threading.Thread(target=self.start)
        self._loop_thread.start()

    def stop(self):
        """Stop the pipeline by terminating the process."""
        if self._process and self._process.poll() is None:
            try:
                self._process.terminate()
            except Exception:
                pass  # The process might have already terminated
        self._process = None

    def join(self):
        """Wait for the pipeline process and thread to finish."""
        if self._process:
            self._process.wait()
        if self._loop_thread:
            self._loop_thread.join()
        self._loop_thread = None

    def close(self):
        """Stop and clean up the pipeline."""
        self.stop()
        self.join()
