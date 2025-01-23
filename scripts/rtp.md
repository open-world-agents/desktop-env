```
$env:GST_PLUGIN_PATH="C:\Users\MilkClouds\Documents\GitHub\desktop-env\custom_plugin"
$host="localhost"
$port=7984

gst-launch-1.0 -e -v `
mpegtsmux name=mux ! rtpmp2tpay ! udpsink host=$host port=$port `
wasapi2src do-timestamp=true loopback=true low-latency=true `
    ! audioconvert `
    ! mfaacenc `
    ! queue `
    ! mux. `
d3d11screencapturesrc show-cursor=true do-timestamp=true `
    ! videorate drop-only=true `
    ! "video/x-raw(memory:D3D11Memory),framerate=0/1,max-framerate=60/1" `
    ! tee name=t `
t. ! queue leaky=downstream `
    ! d3d11download `
    ! videoconvert `
    ! "video/x-raw,format=BGRA" `
    ! appsink name=appsink sync=true max-buffers=1 drop=true emit-signals=true `
t. ! queue leaky=downstream `
    ! d3d11download `
    ! videoconvert `
    ! "video/x-raw,format=BGRA" `
    ! fpsdisplaysink video-sink=fakesink `
t. ! queue `
    ! d3d11convert `
    ! mfh264enc `
    ! h264parse `
    ! queue `
    ! mux. `
utctimestampsrc interval=1 do-timestamp=true `
    ! subparse `
    ! queue `
    ! mux.
```



```
$host="localhost"
$port=7984

gst-launch-1.0 -e -v `
udpsrc port=$port `
    ! "application/x-rtp, media=(string)application, clock-rate=(int)90000, encoding-name=(string)MP2T" `
    ! rtpmp2tdepay `
    ! tsdemux name=demux `
demux. ! queue `
       ! h264parse `
       ! avdec_h264 `
       ! videoconvert `
       ! autovideosink sync=false `
demux. ! queue `
       ! aacparse `
       ! avdec_aac `
       ! autoaudiosink sync=false `
demux. ! queue `
       ! subparse `
       ! subtitleoverlay `
       ! autovideosink sync=false
```