import time

from desktop_env import Desktop, DesktopArgs
from desktop_env.msg import FrameStamped
from desktop_env.windows_capture import construct_pipeline


def on_frame_arrived(frame: FrameStamped):
    latency = (time.time_ns() - frame.timestamp_ns) / 1e6
    print(f"Frame arrived at {frame.timestamp_ns}, latency: {latency:.2f} ms")
    frame_arr = frame.frame_arr  # (W, H, RGBA)


def on_event(event):
    print(event)


if __name__ == "__main__":
    args = DesktopArgs(
        windows_capture_args={
            "on_frame_arrived": on_frame_arrived,
            "pipeline_description": construct_pipeline(
                window_name=None,  # you may substring of the window name
                monitor_idx=None,  # you may specify the monitor index
                framerate="60/1",
            ),
        },
        window_publisher_args={"callback": on_event},
        control_publisher_args={"keyboard_callback": on_event, "mouse_callback": on_event},
    )
    desktop = Desktop.from_args(args)

    try:
        # Option 1. Start the pipeline in the current thread (blocking)
        # desktop.start()

        # Option 2. Start the pipeline in a separate thread (non-blocking)
        desktop.start_free_threaded()
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        desktop.stop()
        desktop.join()
        desktop.close()
