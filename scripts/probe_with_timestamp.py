import gi

gi.require_version("Gst", "1.0")
import datetime
import time

from gi.repository import GObject, Gst
from loguru import logger
from tqdm import tqdm

Gst.init(None)
pbar = tqdm(unit="frames", dynamic_ncols=True)


def on_buffer(pad: Gst.Pad, info: Gst.PadProbeInfo, user_data) -> Gst.PadProbeReturn:
    buffer = info.get_buffer()
    pts = buffer.pts
    if pts != Gst.CLOCK_TIME_NONE:
        # Get the pipeline's clock. Ref: https://gstreamer.freedesktop.org/documentation/gstreamer/gstelement.html?gi-language=python
        pipeline: Gst.Pipeline = user_data["pipeline"]
        clock = pipeline.get_clock()
        assert clock.props.clock_type == Gst.ClockType.MONOTONIC
        elapsed_time_from_playing = clock.get_time() - pipeline.get_base_time()
        latency = elapsed_time_from_playing - pts

        # Print the latency in milliseconds
        pbar.set_postfix(latency=f"{latency / Gst.MSECOND:.2f} ms")
        pbar.update(1)

        frame_time_in_monotonic = pts + pipeline.get_base_time()
        frame_time_in_utc = frame_time_in_monotonic + (time.time_ns() - time.monotonic_ns())
        # Convert nanoseconds to seconds and get UTC time
        utc_time = datetime.datetime.fromtimestamp(frame_time_in_utc / Gst.SECOND)
        # Write the UTC timestamp to the file
        with open("timestamps.txt", "a") as f:
            f.write(f"{utc_time.isoformat()}\n")
    return Gst.PadProbeReturn.OK


def main():
    # Create the pipeline with named elements
    pipeline_str = (
        "d3d11screencapturesrc show-cursor=True name=src do-timestamp=True ! "
        "videorate name=videorate ! video/x-raw,framerate=30/1 ! "
        "videoconvert ! x264enc ! "
        "mp4mux fragment-duration=2000 ! "
        "filesink location=output.mp4"
    )

    pipeline = Gst.parse_launch(pipeline_str)

    # Get the videorate element by name
    videorate = pipeline.get_by_name("videorate")
    if not videorate:
        print("Could not get videorate element")
        return

    # Get the src pad of the videorate element
    src_pad = videorate.get_static_pad("src")
    if not src_pad:
        print("Could not get src pad of videorate")
        return

    # Add the pad probe to intercept buffers
    user_data = {"pipeline": pipeline}
    src_pad.add_probe(Gst.PadProbeType.BUFFER, on_buffer, user_data)

    # Start the pipeline
    ret = pipeline.set_state(Gst.State.PLAYING)
    if ret == Gst.StateChangeReturn.FAILURE:
        print("Failed to set pipeline to PLAYING state")
        return

    # Run the main loop
    loop = GObject.MainLoop()
    try:
        loop.run()
    except KeyboardInterrupt:
        pass
    finally:
        print("Shutting down the pipeline")
        # Clean up
        pipeline.send_event(Gst.Event.new_eos())
        bus = pipeline.get_bus()
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
        pipeline.set_state(Gst.State.NULL)
        loop.quit()


if __name__ == "__main__":
    main()
