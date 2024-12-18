# desktop-env

A real-time, high-frequency, real-world desktop environment that is suitable for desktop-based ML development (agents, world models, etc.)

Currently, in open-source agent research, three things are missing:

1. **Open-source environments**
2. **Open-source data**
3. **Open-source research**

`desktop-env` addresses (1) the issue of open-source environments by providing a desktop-based environment, and solves (2) the problem of open-source data by offering a `recorder`. We plan to tackle (3) the issue of open-source research in a new repository in the future.

## Key Features

- **real-time**: supports **sub-1ms** latency for screen capture
- **high-frequency**: supports **over 144fps** screen capture with **almost no** CPU/GPU load, utilizing Windows API(`DXGI/WGC`, utilizing extremely powerful and versatile framework for creating streaming media applications: `gstreamer`)
- **real-world**: Because it is identical to the desktop environment that humans actually use, you can collect data obtained from human desktop usage directly and utilize it as is for agents

Currently, `desktop-env` supports following desktop events:

- screen: screen on your monitor, you can specific monitor index, windows name, framerate
- keyboard/mouse: it can capture your keyboard/mouse input and also can input them
- window: active window's name, bbox, hWnd

Currently, `desktop-env` supports the following OS: **Windows**. Since the main goal of `desktop-env` is to provide an efficiently optimized environment capable of running even real-time games, support for other operating systems will be added a bit more slowly.

## Screen Capture Benchmark

Measured in i5-11400, GTX 1650.
Except `desktop-env`, the time is measure by `python3 -m pyscreenshot.check.speedtest --childprocess 0` of [pyscreenshot](https://github.com/ponty/pyscreenshot)

| Library       | Average Time per Frame | Times Slower than `desktop-env` |
|---------------|------------------------|---------------------------------|
| `desktop-env` | **5.7 ms**             | 1×                              |
| `pyscreenshot`| 33 ms                  | 5.8×                            |
| `PIL`         | 34 ms                  | 6.0×                            |
| `MSS`         | 37 ms                  | 6.5×                            |
| `PyQt5`       | 137 ms                 | 24×                             |


## Example usage

For full runnable script, see `scripts/minimal_example.py`
```py
from desktop_env import Desktop, DesktopArgs
from desktop_env.msg import FrameStamped
from desktop_env.windows_capture import construct_pipeline

def on_frame_arrived(frame: FrameStamped):
    # Frame arrived at 1733368006665481600, latency: 0.00 ms, frame shape: (2000, 3000, 4)


def on_event(event):
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

```


## Recorder

We also provide a simple `recorder` for collecting desktop data. We'll provide this within few week.


## Installation

You should install `poetry` first: see [poetry installation guide](https://python-poetry.org/docs/)


You can install `desktop-env` with following command.

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



## TODOs

- [ ] validate overall modality's matching in multi-monitor setting
- [ ] remote desktop control demo that wraps up Desktop and expose network interface through udp/tcp, http/websocket, ...
- [ ] support various video format besides raw RGBA (jpeg, h264, ...)
- [ ] multi-os support(Linux & MacOS)
- [ ] language interface implementation to supports existing many, many langauge based desktop agents