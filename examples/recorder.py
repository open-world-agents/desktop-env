"""
This example demonstrates how to use the `Recorder` submodule to record the desktop screen.

For more information, run `examples/recorder.py` with `--help` option.
"""

import time
from typing import Optional

import orjson
import typer
from loguru import logger
from pydantic import BaseModel
from tqdm import tqdm
from typing_extensions import Annotated

from desktop_env import Desktop, DesktopArgs
from desktop_env.recorder import RecorderArgs

# how to use loguru with tqdm: https://github.com/Delgan/loguru/issues/135
logger.remove()
logger.add(lambda msg: tqdm.write(msg, end=""), colorize=True)

logger.enable("desktop_env")  # it's optional to enable the logger; just for debugging


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


def main(
    file_location: Annotated[str, typer.Argument(help="The location of the output file, use `.mkv` extension.")],
    *,
    record_audio: Annotated[bool, typer.Option(help="Whether to record audio")] = True,
    record_video: Annotated[bool, typer.Option(help="Whether to record video")] = True,
    record_timestamp: Annotated[bool, typer.Option(help="Whether to record timestamp")] = True,
    window_name: Annotated[
        Optional[str], typer.Option(help="The name of the window to capture, substring of window name is supported")
    ] = None,
    monitor_idx: Annotated[Optional[int], typer.Option(help="The index of the monitor to capture")] = None,
):
    assert file_location.endswith(".mkv"), "The output file must have `.mkv` extension."
    args = DesktopArgs(
        submodules=[
            {
                "module": "desktop_env.recorder.Recorder",
                "args": RecorderArgs(
                    filesink_location=file_location,
                    record_audio=record_audio,
                    record_video=record_video,
                    record_timestamp=record_timestamp,
                    window_name=window_name,
                    monitor_idx=monitor_idx,
                ),
            },
            {
                "module": "desktop_env.window_publisher.WindowPublisher",
                "args": {"callback": window_publisher_callback},
            },
            {
                "module": "desktop_env.control_publisher.ControlPublisher",
                "args": {
                    "keyboard_callback": control_publisher_callback,
                    "mouse_callback": control_publisher_callback,
                },
            },
        ]
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

        # or you may use desktop.stop_join_close()


if __name__ == "__main__":
    typer.run(main)
