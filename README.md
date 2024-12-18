# 🖥️ desktop-env

**`desktop-env`** is a cutting-edge, **real-time** desktop environment designed specifically for desktop-based machine learning development — perfect for creating agents, world models, and more.

---

## 🎯 Why Choose `desktop-env`?

In the realm of open-source agent research, three critical components are often missing:

1. **🌐 Open-Source Environments**
2. **📊 Open-Source Data**
3. **🔎 Open-Source Research Codebases & Repositories**

`desktop-env` is here to fill these gaps:

- 🖥️ **Open-Source Environment**: Provides a rich, desktop-based environment identical to what humans use daily.
- 📈 **Data Recorder**: Includes a built-in [recorder](examples/recorder/) to capture and utilize real human desktop interactions.
- 🤝 **Future Research Collaboration**: Plans are underway to foster open-source research in *a new repository*.

---

## 🔑 Key Features

- ⚡ **Real-Time Performance**: Achieve **sub-1ms latency** in screen capture.
- 🎥 **High-Frequency Capture**: Supports **over 144 FPS** screen recording with **minimal CPU/GPU load**.
  - Utilizes Windows APIs (`DXGI/WGC`) and the powerful [GStreamer](https://gstreamer.freedesktop.org/) framework, which differ from `PIL.ImageGrab`, `mss`, ...
- 🖱️ **Authentic Desktop Interaction**: Work within the exact desktop environment used by real users.

### Supported Desktop Events & Interfaces:

- 📺 **Screen**: Capture your monitor screen; specify monitor index, window name, framerate.
- ⌨️🖱️ **Keyboard/Mouse**: Capture and input keyboard and mouse events.
- 🪟 **Window**: Get active window's name, bounding box, and handle (`hWnd`).

🚨 **Note**: Currently, `desktop-env` supports **Windows** OS. Since the main goal is to provide an efficiently optimized environment capable of running even real-time games, support for other operating systems will be added gradually.

---

## 🚀 Blazing Performance

`desktop-env` outperforms other screen capture libraries:

| Library         | Avg. Time per Frame | Relative Speed     |
|-----------------|---------------------|--------------------|
| **desktop-env** | **5.7 ms**          | **⚡1× (Fastest)**|
| `pyscreenshot`  | 33 ms               | 🚶‍♂️ 5.8× slower    |
| `PIL`           | 34 ms               | 🚶‍♂️ 6.0× slower    |
| `MSS`           | 37 ms               | 🚶‍♂️ 6.5× slower    |
| `PyQt5`         | 137 ms              | 🐢 24× slower      |

*Measured on i5-11400, GTX 1650.* Not only is FPS measured, but CPU/GPU resource usage is also **significantly lower**.

---

## 💡 Examples

### 🎮 Working Demo

https://github.com/user-attachments/assets/4aee4580-179d-4e57-b876-0dd5256bb9c5

For more details with self-contained running source code, see [examples/typing_agent](https://github.com/open-world-agents/desktop-env/tree/main/examples/typing_agent).

### 👩‍💻 Example Usage

For full runnable scripts, see `scripts/minimal_example.py`, `scripts/main.py`.

```python
from desktop_env import Desktop, DesktopArgs
from desktop_env.msg import FrameStamped
from desktop_env.windows_capture import construct_pipeline

def on_frame_arrived(frame: FrameStamped):
    # Frame arrived at {frame.timestamp}, latency: {latency} ms, frame shape: {frame.shape}
    pass

def on_event(event):
    # event_type='{event.type}' event_data={event.data} event_time={event.time} device_name='{event.device}'
    # title='{event.title}' rect={event.rect} hWnd={event.hWnd}
    pass

if __name__ == "__main__":
    args = DesktopArgs(
        windows_capture_args={
            "on_frame_arrived": on_frame_arrived,
            "pipeline_description": construct_pipeline(
                window_name=None,  # you may specify a substring of the window name
                monitor_idx=None,  # you may specify the monitor index
                framerate="60/1",
            ),
        },
        window_publisher_args={"callback": on_event},
        control_publisher_args={"keyboard_callback": on_event, "mouse_callback": on_event},
    )
    desktop = Desktop.from_args(args)

    try:
        # Option 1: Start the pipeline in the current thread (blocking)
        # desktop.start()

        # Option 2: Start the pipeline in a separate thread (non-blocking)
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

---

## 🛠️ Installation

**Prerequisites**: Install `poetry` first. See the [Poetry Installation Guide](https://python-poetry.org/docs/).

Install `desktop-env` with the following commands:

```bash
conda install -c conda-forge pygobject -y
conda install -c conda-forge gstreamer gst-plugins-base gst-plugins-good gst-plugins-bad gst-plugins-ugly -y

poetry install
```

🚨 **Note**: Installing `pygobject` with `pip` causes the error:
```
..\meson.build:31:9: ERROR: Dependency 'gobject-introspection-1.0' is required but not found.
```

After installation, verify it with the following commands:

- Ensure GStreamer version >= 1.24.6
- Confirm the Direct3D11 plugin is installed

```bash
$ conda list gst-*
# packages in environment at C:\Users\...\miniconda3\envs\agent:
#
# Name                    Version                   Build  Channel
gst-plugins-bad           1.24.6               he11079b_0    conda-forge
gst-plugins-base          1.24.6               hb0a98b8_0    conda-forge
gst-plugins-good          1.24.6               h3b23867_0    conda-forge
gst-plugins-ugly          1.24.6               ha7af72c_0    conda-forge
gstreamer                 1.24.6               h5006eae_0    conda-forge

$ gst-inspect-1.0.exe d3d11
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

---

## 📝 TODOs

- [ ] 🖥️ Validate overall modality matching in multi-monitor setting
- [ ] 🌐 Implement remote desktop control demo that wraps up Desktop and exposes network interface through UDP/TCP, HTTP/WebSocket, etc.
- [ ] 🎥 Support various video formats besides raw RGBA (JPEG, H.264, ...)
- [ ] 🐧🍎 Add multi-OS support (Linux & macOS)
- [ ] 💬 Implement language interfaces to support desktop agents written in various languages

---