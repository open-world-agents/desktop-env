import functools
import inspect
import time

import cv2
import orjson
import yaml
from loguru import logger
from pydantic import BaseModel
from tqdm import tqdm

from desktop_env import Desktop, DesktopArgs
from desktop_env.msg import FrameStamped
from desktop_env.windows_capture import construct_pipeline

# how to use loguru with tqdm: https://github.com/Delgan/loguru/issues/135
logger.remove()
logger.add(lambda msg: tqdm.write(msg, end=""), colorize=True)

logger.enable("desktop_env")  # it's optional to enable the logger; just for debugging


def on_frame_arrived(frame: FrameStamped):
    # Every 2 seconds, print the timestamp and latency of the frame
    now = time.time_ns()
    on_frame_arrived.last_printed = getattr(on_frame_arrived, "last_printed", 0)
    on_frame_arrived.count = getattr(on_frame_arrived, "count", 0) + 1
    if now - on_frame_arrived.last_printed >= 2e9:
        latency = (now - frame.timestamp_ns) / 1e6
        logger.info(f"Frame arrived at {frame.timestamp_ns}, latency: {latency:.2f} ms")

        frame_arr = frame.frame_arr

        # save into file
        # cv2.imwrite(f"frame_{on_frame_arrived.count:02d}.jpg", frame_arr)
        on_frame_arrived.last_printed = now


class BagEvent(BaseModel):
    timestamp_ns: int
    event_src: str
    event_data: bytes


def write_event_into_jsonl(event, source=None):
    # you can find where the event is coming from. e.g. where the calling this function
    # frame = inspect.currentframe().f_back

    with open("event.jsonl", "ab") as f:
        if isinstance(event, BaseModel):
            event_data = event.model_dump_json().encode("utf-8")
        else:
            event_data = orjson.dumps(event)
        bag_event = BagEvent(timestamp_ns=time.time_ns(), event_src=source, event_data=event_data)
        f.write(bag_event.model_dump_json().encode("utf-8") + b"\n")


def window_publisher_callback(event):
    write_event_into_jsonl(event, source="window_publisher")


def control_publisher_callback(event):
    write_event_into_jsonl(event, source="control_publisher")


if __name__ == "__main__":
    # Example 1. Capture the entire screen and discard all other events
    # args = DesktopArgs(
    #     windows_capture_args={
    #         "on_frame_arrived": on_frame_arrived,
    #         "pipeline_description": construct_pipeline(monitor_idx=1),
    #     },
    #     window_publisher_args={"callback": "desktop_env.args.callback_sink"},
    #     control_publisher_args={
    #         "keyboard_callback": "desktop_env.args.callback_sink",
    #         "mouse_callback": "desktop_env.args.callback_sink",
    #     },
    # )
    # Example 2. Capture a specific window and save all events into a JSONL file
    args = DesktopArgs(
        windows_capture_args={
            "on_frame_arrived": on_frame_arrived,
            "pipeline_description": construct_pipeline(
                window_name=None,  # you may substring of the window name
                monitor_idx=None,  # you may specify the monitor index
                framerate="60/1",
            ),
        },
        window_publisher_args={"callback": window_publisher_callback},
        control_publisher_args={
            "keyboard_callback": control_publisher_callback,
            "mouse_callback": control_publisher_callback,
        },
    )
    args.to_yaml("desktop_args.yaml")
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

        # or you may use desktop.stop_join_close()
