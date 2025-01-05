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
        additional_parameter_for_screencap: Additional parameter for screen capturing.
        framerate: The frame rate of the video.
        output_format: The output format of the video. Either "raw" or "jpeg".
    """
    os_name = platform.system()

    # Initialize base pipeline based on OS
    if os_name == "Windows":
        pipeline_parts = ["d3d11screencapturesrc show-cursor=TRUE"]

        # Add window handle if window name is provided
        if window_name:
            window_info = get_window_by_title(window_name)
            pipeline_parts.append(f"window-handle={window_info.hWnd}")

    elif os_name == "Darwin":
        # For macOS, use avfvideosrc with specific capture settings
        # Reference: gst-inspect-1.0 avfvideosrc shows available properties
        pipeline_parts = ["avfvideosrc", "capture-screen=true", "capture-screen-cursor=true", "do-timestamp=true"]

        # Add monitor selection if specified
        if monitor_idx is not None:
            pipeline_parts.append(f"device-index={monitor_idx}")

        # Add specific format for macOS
        pipeline_parts.append("! video/x-raw,format=UYVY")
        pipeline_parts.append("! videoconvert n-threads=4")  # Use multiple threads for conversion

    elif os_name == "Linux":
        pipeline_parts = ["ximagesrc"]

    else:
        raise NotImplementedError(f"Unsupported platform: {os_name}")

    # Add monitor index if specified
    if monitor_idx is not None:
        if os_name == "Darwin":
            pipeline_parts.append(f"device-index={monitor_idx}")
        else:
            pipeline_parts.append(f"monitor-index={monitor_idx}")

    # Add any additional parameters
    if additional_parameter_for_screencap:
        pipeline_parts.append(additional_parameter_for_screencap)

    # Add common pipeline elements with OS-specific adjustments
    if os_name != "Darwin":  # macOS already has these settings
        pipeline_parts.extend(["do-timestamp=True", "videorate drop-only=True"])

    # Add format settings
    if os_name == "Windows":
        pipeline_parts.append(f"video/x-raw(memory:D3D11Memory),framerate=0/1,max-framerate={framerate}")
        pipeline_parts.append("d3d11download")
    elif os_name == "Linux":
        pipeline_parts.append(f"video/x-raw,framerate={framerate}")
        pipeline_parts.append("videoconvert")

    # Add output format for non-macOS platforms
    # macOS already has the correct format conversion in place
    if os_name != "Darwin":
        pipeline_parts.append(output_format_to_element(output_format))

    # Add sink with platform-specific settings
    if os_name == "Darwin":
        pipeline_parts.append("! appsink name=appsink max-buffers=2 drop=true sync=false")
    else:
        pipeline_parts.append("appsink name=appsink max-buffers=1 drop=true")

    # Join all parts with appropriate separators
    if os_name == "Darwin":
        # macOS uses space-separated parameters for the same element
        pipeline_str = " ".join(pipeline_parts)
    else:
        # Other platforms use ! to separate elements
        pipeline_str = " ! ".join(pipeline_parts)

    assert "appsink" in pipeline_str, "appsink element is not found in the pipeline description."
    return pipeline_str
