import platform
import sys
from typing import Literal, Optional

from ..utils import get_window_by_title


def output_format_to_element(output_format: Literal["raw", "jpeg"]) -> str:
    """Convert the output format to the corresponding GStreamer element."""
    if output_format == "raw":
        return "video/x-raw,format=BGRA"  # Caution: alpha channel is valid when capturing the screen.
    # elif output_format == "jpeg": # TODO: support jpeg encoding
    #     return "jpegenc"
    else:
        raise ValueError(f"Unsupported output format: {output_format}")


def construct_pipeline(
    window_name: Optional[str] = None,
    monitor_idx: Optional[int] = None,
    additional_parameter_for_screencap="",
    framerate="30/1",
    output_format: Literal["raw", "jpeg"] = "raw",
) -> str:
    """Construct a GStreamer pipeline for screen capturing.
    Args:
        window_name: The name of the window to capture. If None, the entire screen will be captured.
        monitor_idx: The index of the monitor to capture. If None, the primary monitor will be captured.
        additional_parameter_for_screencap: Additional parameter for screen capturing. e.g. window-handle=0x21466, monitor-index=1, etc.
        framerate: The frame rate of the video.
        output_format: The output format of the video. Either "raw" or "jpeg".
    """
    if platform.system() == "Windows":
        pipeline_src = "d3d11screencapturesrc show-cursor=TRUE"
        # TODO: test whether d3d11testsrc is valid in other OS
    elif platform.system() == "Linux":
        pipeline_src = "ximagesrc"
    elif platform.system() == "Darwin":
        pipeline_src = "avfvideosrc capture-screen=true"
    else:
        print("Unsupported platform.")
        sys.exit(1)

    src_parameter = ""
    if window_name is not None:
        src_parameter += f" window-handle={get_window_by_title(window_name).hWnd}"
    if monitor_idx is not None:
        src_parameter += f" monitor-index={monitor_idx}"

    assert isinstance(framerate, str), "framerate must be a string, now. (TODO: support other types)"

    pipeline_description = (
        f"{pipeline_src} {src_parameter} {additional_parameter_for_screencap} ! "
        "videorate ! "
        f"video/x-raw,framerate={framerate} ! "
        "videoconvert ! "
        f"{output_format_to_element(output_format)} ! "
        "appsink name=appsink max-buffers=1 drop=true"
    )
    # max-buffers=1 drop=true: Drop the frame if the buffer is full. it is necessary to prevent memory boom.

    assert "appsink" in pipeline_description, "appsink element is not found in the pipeline description."
    return pipeline_description
