import time

from loguru import logger
from tqdm import tqdm

from desktop_env import Desktop, DesktopArgs
from desktop_env.msg import FrameStamped
from desktop_env.windows_capture import construct_pipeline

# how to use loguru with tqdm: https://github.com/Delgan/loguru/issues/135
logger.remove()
logger.add(lambda msg: tqdm.write(msg, end=""), colorize=True)


def on_frame_arrived(frame: FrameStamped):
    latency = (time.time_ns() - frame.timestamp_ns) / 1e6
    logger.debug(
        f"Frame arrived at {frame.timestamp_ns}, latency: {latency:.2f} ms, frame shape: {frame.frame_arr.shape}"
    )
    #  Frame arrived at 1733368006665481600, latency: 0.00 ms, frame shape: (2000, 3000, 4)


def on_event(event):
    logger.debug(event)
    # event_type='on_press' event_data=162 event_time=1733368006688750600 device_name='keyboard'
    # title='windows_capture.py - desktop-env - Visual Studio Code' rect=(527, -1096, 2479, -32) hWnd=1379722
    # event_type='on_move' event_data=(1323, -154) event_time=1733368048442994300 device_name='mouse'


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
