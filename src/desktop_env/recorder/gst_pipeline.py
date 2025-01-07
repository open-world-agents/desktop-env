from typing import Optional

from ..utils import get_window_by_title


def construct_pipeline(
    filesink_location: str,
    *,
    record_audio: bool = True,
    record_video: bool = True,
    record_timestamp: bool = True,
    enable_appsink: bool = False,
    enable_fpsdisplaysink: bool = True,
    window_name: Optional[str] = None,
    monitor_idx: Optional[int] = None,
) -> str:
    """Construct a GStreamer pipeline for screen capturing.
    Args:
        filesink_location: The location of the output file.
        record_audio: Whether to record audio.
        record_video: Whether to record video.
        record_timestamp: Whether to record timestamp.
        enable_appsink: Whether to enable appsink.
        enable_fpsdisplaysink: Whether to enable fpsdisplaysink.
        window_name: The name of the window to capture. If None, the entire screen will be captured.
        monitor_idx: The index of the monitor to capture. If None, the primary monitor will be captured.
    """
    assert enable_appsink or enable_fpsdisplaysink, "At least one of appsink and fpsdisplaysink must be enabled."

    pipeline_description = []
    pipeline_description += [f"matroskamux name=mux ! filesink location={filesink_location}"]

    if record_audio:
        pipeline_description += [
            "wasapi2src do-timestamp=true loopback=true low-latency=true ! audioconvert ! mfaacenc ! queue ! mux."
        ]
    if record_video:
        src_parameter = ""
        if window_name is not None:
            src_parameter += f" window-handle={get_window_by_title(window_name).hWnd}"
        if monitor_idx is not None:
            src_parameter += f" monitor-index={monitor_idx}"

        pipeline_description += [
            f"d3d11screencapturesrc show-cursor=true {src_parameter} do-timestamp=true ! "
            "videorate drop-only=true ! video/x-raw(memory:D3D11Memory),framerate=0/1,max-framerate=60/1 ! "
            "tee name=t "
            "t. ! queue ! d3d11convert ! mfh264enc ! h264parse ! queue ! mux."
        ]
    if record_timestamp:
        pipeline_description += ["utctimestampsrc interval=1 ! subparse ! queue ! mux."]

    if enable_appsink:
        pipeline_description += [
            "t. ! queue leaky=downstream ! d3d11download ! videoconvert ! video/x-raw,format=BGRA ! "
            "appsink name=appsink sync=true max-buffers=1 drop=true emit-signals=true"
        ]
    if enable_fpsdisplaysink:
        pipeline_description += [
            "t. ! queue leaky=downstream ! d3d11download ! videoconvert ! video/x-raw,format=BGRA ! "
            "fpsdisplaysink video-sink=fakesink"
        ]

    pipeline_str = " ".join(pipeline_description)
    return pipeline_str
