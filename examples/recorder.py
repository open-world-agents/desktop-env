"""
This example demonstrates how to use the `Recorder` submodule to record the desktop screen.

"""

import time
from typing import Optional

import typer
from loguru import logger
from tqdm import tqdm
from typing_extensions import Annotated

from desktop_env import Desktop, DesktopArgs
from desktop_env.recorder import RecorderArgs

# how to use loguru with tqdm: https://github.com/Delgan/loguru/issues/135
logger.remove()
logger.add(lambda msg: tqdm.write(msg, end=""), colorize=True)

logger.enable("desktop_env")  # it's optional to enable the logger; just for debugging


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
            }
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
