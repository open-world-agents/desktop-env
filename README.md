
# Installation
```
conda install -c conda-forge pygobject -y
conda install -c conda-forge gstreamer gst-plugins-base gst-plugins-good gst-plugins-bad gst-plugins-ugly -y

poetry install
```

Note: Installing `pygobject` with pip causes `..\meson.build:31:9: ERROR: Dependency 'gobject-introspection-1.0' is required but not found.`

After installation, you may verify installation with following comand.
- gstreamer version >= 1.24.6
- Direct3D11 plugin is installed

```
$ conda list gst-*
# packages in environment at C:\Users\...\miniconda3\envs\agent:
#
# Name                    Version                   Build  Channel
gst-plugins-bad           1.24.6               he11079b_0    conda-forge
gst-plugins-base          1.24.6               hb0a98b8_0    conda-forge
gst-plugins-good          1.24.6               h3b23867_0    conda-forge
gst-plugins-ugly          1.24.6               ha7af72c_0    conda-forge
gstreamer                 1.24.6               h5006eae_0    conda-forge
$  gst-inspect-1.0.exe d3d11
Plugin Details:
  Name                     d3d11
  Description              Direct3D11 plugin
  Filename                 C:\Users\...\miniconda3\envs\agent\Library\lib\gstreamer-1.0\gstd3d11.dll
  Version                  1.24.6
  License                  LGPL
  Source module            gst-plugins-bad
  Documentation            https://gstreamer.freedesktop.org/documentation/d3d11/
  Source release date      2024-07-29
  Binary package           GStreamer Bad Plug-ins source release
  Origin URL               Unknown package origin

  d3d11colorconvert: Direct3D11 Colorspace Converter
  d3d11compositor: Direct3D11 Compositor
...
  d3d11screencapturesrc: Direct3D11 Screen Capture Source
...
```

# Usage

```py
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
        desktop.close()
```


# TODOs

- MUSTs
[] validate overall modality's matching in multi-monitor setting

- MAYs
[] remote desktop control demo that wraps up Desktop and expose network interface through udp/tcp, http/websocket, ...
[] support various video format besides raw RGBA (jpeg, h264, ...)
[] multi-os support(Linux & MacOS)
[] pydantic BaseSettings https://docs.pydantic.dev/latest/concepts/pydantic_settings/