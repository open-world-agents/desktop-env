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
    args_cls = WindowsCaptureArgs

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
        self.pipeline: Gst.Pipeline = Gst.parse_launch(pipeline_description)

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
        ret = self.pipeline.set_state(Gst.State.PLAYING)
        if ret == Gst.StateChangeReturn.FAILURE:
            bus = self.pipeline.get_bus()
            msg = bus.timed_pop_filtered(Gst.CLOCK_TIME_NONE, Gst.MessageType.ERROR)
            err, debug = msg.parse_error()
            print(f"Failed to set pipeline to PLAYING state, got {ret}")
            print(f"Error: {err}, Debug: {debug}")
            return
        self.loop.run()

    def start_free_threaded(self):
        """Start the pipeline in a separate thread. This function will not block the current thread."""

        self._loop_thread = threading.Thread(target=self.start)
        self._loop_thread.start()

    # TODO: verify whether stop-join-close lifecycle is correct
    def stop(self):
        self.pipeline.send_event(Gst.Event.new_eos())
        bus = self.pipeline.get_bus()
        while True:
            msg = bus.timed_pop_filtered(Gst.CLOCK_TIME_NONE, Gst.MessageType.EOS | Gst.MessageType.ERROR)
            if msg:
                if msg.type == Gst.MessageType.EOS:
                    print("Received EOS signal, shutting down gracefully.")
                    break
                elif msg.type == Gst.MessageType.ERROR:
                    err, debug = msg.parse_error()
                    print("Error received:", err, debug)
                    break
        self.pipeline.set_state(Gst.State.NULL)

    def join(self): ...

    def close(self):
        self.loop.quit()
        if hasattr(self, "_loop_thread"):
            self._loop_thread.join()
        self.pbar.close()

    def __get_frame_time_utc(self, pts):
        assert pts != Gst.CLOCK_TIME_NONE

        # Get the pipeline's clock. Ref: https://gstreamer.freedesktop.org/documentation/gstreamer/gstelement.html?gi-language=python
        clock = self.pipeline.get_clock()
        assert clock.props.clock_type == Gst.ClockType.MONOTONIC
        elapsed_time_from_playing = clock.get_time() - self.pipeline.get_base_time()
        latency = elapsed_time_from_playing - pts

        # TODO: report latency step-by-step, separating the gstreamer's latency and others
        # Print the latency in milliseconds
        # print(f"Latency: {latency / Gst.MSECOND:.2f} ms")

        # frame_time_in_monotonic = pts + self.pipeline.get_base_time()
        # frame_time_in_utc = frame_time_in_monotonic + (time.time_ns() - time.monotonic_ns())
        frame_time_in_utc = time.time_ns() - latency

        # Convert nanoseconds to seconds and get UTC time
        import datetime

        utc_time = datetime.datetime.fromtimestamp(frame_time_in_utc / Gst.SECOND)

        return frame_time_in_utc

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
        # This width and height may be different with Window's width and height
        width, height, format_ = (
            structure.get_value("width"),
            structure.get_value("height"),
            structure.get_value("format"),
        )
        assert format_ == "BGRA", f"Unsupported format: {format_}"

        # Calculate time difference
        current_time = time.time()
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
                message = FrameStamped(frame_arr=frame_arr, timestamp_ns=self.__get_frame_time_utc(buf.pts))
                self._bandwidth += len(frame_data)

                # Publish the message data
                callback(message)
            finally:
                buf.unmap(mapinfo)

            # Update the tqdm progress bar
            self.pbar.update(1)
        else:
            return Gst.FlowReturn.ERROR

        return Gst.FlowReturn.OK
