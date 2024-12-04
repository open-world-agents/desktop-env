import datetime
import time

import gi

gi.require_version("Gst", "1.0")
from gi.repository import GObject, Gst

Gst.init(None)


def on_buffer(pad: Gst.Pad, info: Gst.PadProbeInfo, user_data) -> Gst.PadProbeReturn:
    buffer = info.get_buffer()
    pts = buffer.pts
    if pts != Gst.CLOCK_TIME_NONE:
        # Get the pipeline's clock
        pipeline: Gst.Pipeline = user_data["pipeline"]
        clock = pipeline.get_clock()
        # Get the absolute timestamp of the buffer
        abs_time = clock.get_time() - pipeline.get_base_time() + pts
        # Convert nanoseconds to seconds and get UTC time
        utc_time = datetime.datetime.utcfromtimestamp(abs_time / Gst.SECOND)

        utc_time = datetime.datetime.utcnow()
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
        # Clean up
        pipeline.set_state(Gst.State.NULL)


if __name__ == "__main__":
    main()
