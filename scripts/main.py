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
        cv2.imwrite(f"frame_{on_frame_arrived.count:02d}.jpg", frame_arr)
        on_frame_arrived.last_printed = now


def write_event_into_jsonl(event):
    with open("event.jsonl", "ab") as f:
        if isinstance(event, BaseModel):
            f.write(event.model_dump_json().encode("utf-8") + b"\n")
        else:
            f.write(orjson.dumps(event) + b"\n")


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
            "pipeline_description": construct_pipeline(monitor_idx=0, framerate="60/1"),
        },
        window_publisher_args={"callback": write_event_into_jsonl},
        control_publisher_args={
            "keyboard_callback": write_event_into_jsonl,
            "mouse_callback": write_event_into_jsonl,
        },
    )
    print(args)
    with open("args.yaml", "w") as f:
        args_json = args.model_dump_json()
        args_yaml = yaml.dump(yaml.safe_load(args_json))
        f.write(args_yaml)
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
        desktop.close()
