
# Installation
```
conda install -c conda-forge pygobject -y
conda install -c conda-forge gstreamer gst-plugins-base gst-plugins-good gst-plugins-bad gst-plugins-ugly -y

poetry install
```

# TODOs

- MUSTs
[] validate overall modality's matching in multi-monitor setting

- MAYs
[] remote desktop control demo that wraps up Desktop and expose network interface through udp/tcp, http/websocket, ...
[] support various video format besides raw RGBA (jpeg, h264, ...)
[] multi-os support(Linux & MacOS)
[] pydantic BaseSettings https://docs.pydantic.dev/latest/concepts/pydantic_settings/