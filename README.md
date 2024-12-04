
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
$ gst-inspect-1.0 d3d11screencapturesrc
Factory Details:
  Rank                     none (0)
  Long-name                Direct3D11 Screen Capture Source
  Klass                    Source/Video
  Description              Captures desktop screen
  Author                   Seungha Yang <seungha@centricular.com>
  Documentation            https://gstreamer.freedesktop.org/documentation/d3d11/d3d11screencapturesrc.html

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

...
```

# TODOs

- MUSTs
[] validate overall modality's matching in multi-monitor setting

- MAYs
[] remote desktop control demo that wraps up Desktop and expose network interface through udp/tcp, http/websocket, ...
[] support various video format besides raw RGBA (jpeg, h264, ...)
[] multi-os support(Linux & MacOS)
[] pydantic BaseSettings https://docs.pydantic.dev/latest/concepts/pydantic_settings/