import gi

gi.require_version("Gst", "1.0")
import functools
import threading
import time
from typing import Callable, Optional

import numpy as np
from gi.repository import GLib, Gst
from tqdm import tqdm

from ..threading import AbstractThread
from .args import WindowsCaptureArgs
from .gst_pipeline import construct_pipeline
from .msg import FrameStamped

# Initialize GStreamer
Gst.init(None)


class WindowsCapture(AbstractThread):
    def __init__(
        self,
        on_frame_arrived: Callable[[FrameStamped], None],
        *,
        pipeline_description: Optional[str] = None,
    ):
        # Data for progress bar
        self.pbar = tqdm(total=None, desc="Producing Frames", unit="frames", dynamic_ncols=True)
        self._bandwidth = 0
        self._last_time = time.time()

        if pipeline_description is None:
            pipeline_description = construct_pipeline()
        self.pipeline = Gst.parse_launch(pipeline_description)

        # Get the appsink element and set properties
        self.appsink = self.pipeline.get_by_name("appsink")
        self.appsink.set_property("emit-signals", True)  # This MUST be True to capture `new-sample` signal
        self.appsink.set_property("sync", True)  # This should be True, I guess

        # Connect to the appsink's new-sample signal
        self.on_frame_arrived = functools.partial(self.__on_new_sample, callback=on_frame_arrived)
        self.appsink.connect("new-sample", self.on_frame_arrived)

        self.loop = GLib.MainLoop()

    @classmethod
    def from_args(cls, args: WindowsCaptureArgs):
        return cls(args.on_frame_arrived, pipeline_description=args.pipeline_description)

    def start(self):
        """Start the pipeline. This function will block the current thread."""
        self.pipeline.set_state(Gst.State.PLAYING)
        self.loop.run()

    def start_free_threaded(self):
        """Start the pipeline in a separate thread. This function will not block the current thread."""

        def start_main_loop(loop):
            """Function to run the GLib MainLoop in a separate thread."""
            loop.run()

        self.pipeline.set_state(Gst.State.PLAYING)
        self._loop_thread = threading.Thread(target=start_main_loop, args=(self.loop,))
        self._loop_thread.start()

    def stop(self):
        self.pipeline.set_state(Gst.State.NULL)

    def join(self):
        if hasattr(self, "_loop_thread"):
            self._loop_thread.join()

    def close(self):
        self.loop.quit()
        self.pbar.close()

    def __on_new_sample(self, sink, callback: Callable):
        """Callback function for the new-sample signal of appsink. Internally calls `self.screen_callback(frame_stamped)`"""

        # Retrieve the sample
        sample: Gst.Sample = sink.emit("pull-sample")
        if sample is None:
            print("Received null sample.")
            return Gst.FlowReturn.ERROR
        buf: Gst.Buffer = sample.get_buffer()

        # Get the caps of the sample
        caps: Gst.Caps = sample.get_caps()
        structure: Gst.Structure = caps.get_structure(0)
        width, height, format_ = (
            structure.get_value("width"),
            structure.get_value("height"),
            structure.get_value("format"),
        )
        # print(f"Received frame: {width}x{height} {format_}")

        current_time = time.time()
        # Calculate time difference
        time_diff = current_time - self._last_time

        # Update bandwidth every second
        if time_diff >= 1.0:
            bandwidth = self._bandwidth / time_diff
            self.pbar.set_postfix(bandwidth=f"{bandwidth/1e6:.2f} MB/s", width=width, height=height, format=format_)
            self._bandwidth = 0
            self._last_time = current_time

        # Get buffer data
        map_result: tuple[bool, Gst.MapInfo] = buf.map(Gst.MapFlags.READ)
        result, mapinfo = map_result
        if result:
            try:
                frame_data: bytes = mapinfo.data  # This is the JPEG image data
                frame_arr = np.frombuffer(frame_data, dtype=np.uint8).reshape((height, width, 4))
            finally:
                buf.unmap(mapinfo)

            message = FrameStamped(frame_arr=frame_arr, timestamp_ns=time.time_ns())
            self._bandwidth += len(frame_data)

            # Publish the message data
            callback(message)

            # Update the tqdm progress bar
            self.pbar.update(1)
        else:
            return Gst.FlowReturn.ERROR

        return Gst.FlowReturn.OK
