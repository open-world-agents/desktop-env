
# Experiment settings
i5-11400, GTX 1650

- FHD: full screen, 1920x1080, monitor-index=0
- small: Task Manager, 1025x577, window-handle=1706308

- mfh264enc: mediafoundation(mf), which is from win32 api
- nvh264enc: nvidia encoder
- x264: cpu encoder

# Experiments

```sh
# useful ingredients(parts)
d3d11screencapturesrc show-cursor=TRUE do-timestamp=True ! videorate drop-only=True
"video/x-raw(memory:D3D11Memory),framerate=0/1,max-framerate=60/1"
queue max-size-time=0 max-size-bytes=0 max-size-buffers=100

# all-in-one command, mf version
gst-launch-1.0.exe -e -v d3d11screencapturesrc show-cursor=TRUE window-handle=1706308 do-timestamp=True ! `
videorate drop-only=True ! "video/x-raw(memory:D3D11Memory),framerate=0/1,max-framerate=60/1" ! `
tee name=t `
t. ! queue leaky=downstream ! d3d11download ! video/x-raw,format=BGRA ! appsink name=appsink max-buffers=1 drop=true `
t. ! queue ! d3d11convert ! mfh264enc ! h264parse ! mp4mux ! filesink location=output.mp4

# nvd3d11h264enc version
gst-launch-1.0.exe -e -v d3d11screencapturesrc show-cursor=TRUE window-handle=1706308 do-timestamp=True ! `
videorate drop-only=True ! "video/x-raw(memory:D3D11Memory),framerate=0/1,max-framerate=60/1" ! `
tee name=t `
t. ! queue leaky=downstream ! d3d11download ! video/x-raw,format=BGRA ! appsink name=appsink max-buffers=1 drop=true `
t. ! queue ! d3d11convert ! nvd3d11h265enc zero-reorder-delay=False ! h264parse ! mp4mux ! filesink location=output.mp4

# all-in-one, nvh264enc version
gst-launch-1.0.exe -e -v d3d11screencapturesrc show-cursor=TRUE window-handle=1706308 do-timestamp=True ! `
videorate drop-only=True ! "video/x-raw(memory:D3D11Memory),framerate=0/1,max-framerate=60/1" ! `
tee name=t `
t. ! queue leaky=downstream ! d3d11download ! video/x-raw,format=BGRA ! appsink name=appsink max-buffers=1 drop=true `
t. ! queue ! d3d11convert ! "video/x-raw(memory:D3D11Memory),format=NV12" ! d3d11download ! nvh264enc ! h264parse ! mp4mux ! filesink location=output.mp4

# all-in-one, x264 version
gst-launch-1.0.exe -e -v d3d11screencapturesrc show-cursor=TRUE window-handle=1706308 do-timestamp=True ! `
videorate drop-only=True ! "video/x-raw(memory:D3D11Memory),framerate=0/1,max-framerate=60/1" ! `
tee name=t `
t. ! queue leaky=downstream ! d3d11download ! video/x-raw,format=BGRA ! appsink name=appsink max-buffers=1 drop=true `
t. ! queue ! d3d11download ! videoconvert ! x264enc ! h264parse ! mp4mux ! filesink location=output.mp4

# all-in-one, x264 version 2. more efficient. this command is not used.
gst-launch-1.0.exe -e -v d3d11screencapturesrc show-cursor=TRUE window-handle=1706308 do-timestamp=True ! `
videorate drop-only=True ! "video/x-raw(memory:D3D11Memory),framerate=0/1,max-framerate=60/1" ! `
d3d11download ! video/x-raw,format=BGRA ! tee name=t `
t. ! queue leaky=downstream ! appsink name=appsink max-buffers=1 drop=true `
t. ! queue ! videoconvert ! x264enc ! mp4mux fragment-duration=2000 ! filesink location=output.mp4
```

# Notes

mfh264enc
- rcmode: default 2(uvbr: Unconstrained variable bitrate)

leaky=downstream: Drop the frame if the buffer is full. since appsink is not guaranteed to consume the frame fastly enough, it is necessary.

# Results

1. vague charecter or not?

ONLY in mediafoundation(mf) small setting, charecter is vague. I guess it is because of lack of through support in mediafoundation(it's win32 api) with regard to various reoslution.

- mf, FHD
    - 15554kbps, 60.06fps
    - no problem
- mf, small
    - 242kbps, 52.38fps
    - cpu 0.25
    - vague character problem
- nvenc, small
    - 547kbps, 41.50fps
    - cpu 0.35
    - color is subtly different. gray color -> black.
- x264, small
    - 256kbps, 42.92fps
    - cpu 0.85
    - no problem

2. resource(cpu/gpu) usage

in mf, nvenv, x264, GPU util have no problem. in x264, cpu usage is too high.

- nvenc, FHD
    - cpu 0.5
- x264, FHD
    - cpu 5.0

# Troubleshooting

1. why is resolution vague in mf?
    - mfh264enc supports only even width/height, which is not mentioned in web docs. (only view-able in `gst-inspect-1.0`)
    - `d3d11scale` and `videoscale` which inputs odd size and reduce (1, 1) in (width, height) make resolution vague.
    - if you adjust width/height to even value by cropping to avoid videoscale, vague resolution issue is gone.
2. why is color subtly different in nv?
    - if you use `NV12` instead of `BGRA`, issue gone.
    - why???

# nvh264enc vs nvd3d11h264enc (vs jpegenc)

cheat sheet
```sh
# see bitrate
ffprobe -v error -select_streams v:0 -show_entries stream=bit_rate -of default=noprint_wrappers=1:nokey=1 .\output.mp4
# see IBP info
ffprobe -v error -select_streams v:0 -show_entries frame=pkt_pts_time,pict_type -of csv .\output.mp4
```

uncompressed bitrate = `1920*1080*3*60*8/10^9=2.98Gb`

- `nvd3d11h264enc`
    - cpu 0.84
    - bitrate 13278282=13.2M = 1/230 of uncompressed bitrate
    - by `ffprobe`, I checked `gop-size=30` is well secured.

```powershell
gst-launch-1.0.exe -e -v d3d11screencapturesrc show-cursor=TRUE do-timestamp=True ! `
videorate drop-only=True ! "video/x-raw(memory:D3D11Memory),framerate=0/1,max-framerate=60/1" ! `
tee name=t `
t. ! queue leaky=downstream ! d3d11download ! video/x-raw,format=BGRA ! appsink name=appsink max-buffers=1 drop=true `
t. ! queue ! d3d11convert ! nvd3d11h264enc zero-reorder-delay=true ! h264parse ! mp4mux ! filesink location=output.mp4
```
- `nvd3d11h264enc`, `gop-size=75`
    - cpu 0.90
    - bitrate 9830642=9M

- same, `gop-size=1`
    - cpu 0.90
    - bitrate 41487120=41M

- `nvh264enc`
    - cpu 0.96
    - bitrate 6306484=6M

```powershell
gst-launch-1.0.exe -e -v d3d11screencapturesrc show-cursor=TRUE do-timestamp=True ! `
videorate drop-only=True ! "video/x-raw(memory:D3D11Memory),framerate=0/1,max-framerate=60/1" ! `
tee name=t `
t. ! queue leaky=downstream ! d3d11download ! video/x-raw,format=BGRA ! appsink name=appsink max-buffers=1 drop=true `
t. ! queue ! d3d11convert ! "video/x-raw(memory:D3D11Memory),format=NV12" ! d3d11download ! nvh264enc ! h264parse ! mp4mux ! filesink location=output.mp4
```

- `nvh264enc`, `gop-size=30`
    - cpu 0.70
    - bitrate 12667576=12M

- `jpegenc`
    - cpu 4.2
    - bitrate 530735671=530M = 1/6 of uncompressed bitrate

```powershell
gst-launch-1.0.exe -e -v d3d11screencapturesrc show-cursor=TRUE do-timestamp=True ! `
videorate drop-only=True ! "video/x-raw(memory:D3D11Memory),framerate=60/1" ! `
tee name=t `
t. ! queue leaky=downstream ! d3d11download ! video/x-raw,format=BGRA ! appsink name=appsink max-buffers=1 drop=true `
t. ! queue ! d3d11download ! videoconvert ! jpegenc ! avimux ! filesink location=output.avi
```