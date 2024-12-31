import gi

gi.require_version("Gst", "1.0")
import sys
from datetime import datetime, timezone

from gi.repository import GLib, Gst
from loguru import logger

Gst.init(None)

"""
gst-launch-1.0 -e -v `
matroskamux name=mux ! filesink location=output.mkv `
wasapi2src do-timestamp=true loopback=true low-latency=true ! audioconvert ! mfaacenc ! queue ! mux. `
d3d11screencapturesrc show-cursor=true do-timestamp=true ! `
videorate drop-only=true ! "video/x-raw(memory:D3D11Memory),framerate=0/1,max-framerate=60/1" ! `
tee name=t `
t. ! queue leaky=downstream ! `
d3d11download ! videoconvert ! video/x-raw,format=BGRA ! `
appsink name=appsink sync=true max-buffers=1 drop=true emit-signals=true `
t. ! queue ! d3d11convert ! "video/x-raw(memory:D3D11Memory),format=NV12" ! nvd3d11h264enc ! h264parse ! queue ! mux. `
utctimestampsrc interval=1 ! subparse ! mux. 

gst-launch-1.0 -e -v `
matroskamux name=mux ! filesink location=output.mkv `
wasapi2src do-timestamp=true loopback=true low-latency=true ! audioconvert ! mfaacenc ! queue ! mux. `
d3d11screencapturesrc show-cursor=true do-timestamp=true ! `
videorate drop-only=true ! "video/x-raw(memory:D3D11Memory),framerate=0/1,max-framerate=60/1" ! `
tee name=t `
t. ! queue leaky=downstream ! `
d3d11download ! videoconvert ! "video/x-raw,format=BGRA" ! `
appsink name=appsink sync=true max-buffers=1 drop=true emit-signals=true `
t. ! queue ! d3d11convert ! mfh264enc ! h264parse ! queue ! mux. `
utctimestampsrc interval=1 do-timestamp=true ! subparse ! queue ! mux. 
"""


def main():
    # Build the pipeline
    pipeline = Gst.parse_launch(
        # sink 1. filesink
        "matroskamux name=mux ! filesink location=output.mkv "
        # src 1. audio
        "wasapi2src do-timestamp=true loopback=true low-latency=true ! audioconvert ! mfaacenc ! queue ! mux. "
        # src 2. video
        "d3d11screencapturesrc show-cursor=true do-timestamp=true ! "
        "videorate drop-only=true ! video/x-raw(memory:D3D11Memory),framerate=0/1,max-framerate=60/1 ! "
        "identity name=1 silent=FALSE ! "
        "tee name=t "
        "t. ! queue ! d3d11convert ! mfh264enc ! h264parse ! queue ! mux. "
        # src 3. subtitle
        "utctimestampsrc interval=1 ! subparse ! queue ! mux. "
        # sink 2. appsink
        "t. ! queue leaky=downstream ! d3d11download ! videoconvert ! video/x-raw,format=BGRA ! "
        "appsink name=appsink sync=true max-buffers=1 drop=true emit-signals=true "
    )

    appsink = pipeline.get_by_name("appsink")
    assert appsink.get_property("emit-signals") is True

    def callback(msg):
        sample: Gst.Sample = msg.emit("pull-sample")
        return Gst.FlowReturn.OK

    appsink.connect("new-sample", callback)

    # Start the pipeline
    ret = pipeline.set_state(Gst.State.PLAYING)
    if ret == Gst.StateChangeReturn.FAILURE:
        bus = pipeline.get_bus()
        msg = bus.timed_pop_filtered(Gst.CLOCK_TIME_NONE, Gst.MessageType.ERROR)
        err, debug = msg.parse_error()
        print(f"Failed to set pipeline to PLAYING state, got {ret}")
        print(f"Error: {err}, Debug: {debug}")
        return

    # Create a GLib Main Loop and run it
    loop = GLib.MainLoop()

    try:
        print("GOGO")
        loop.run()
    except KeyboardInterrupt:
        pass
    finally:
        print("! Shutting down the pipeline")
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
