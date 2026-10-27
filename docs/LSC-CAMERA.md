# LSC / Anyka camera integration

## What is supported

LayerSentra can use an optional local bridge to convert **LSC1-framed H.264** into
JPEG snapshots. The secondary camera then uses the same region of interest,
masks, AI model, thresholds, event history and decision engine as other cameras.
This is a software bridge, not a universal LSC firmware installer or ONVIF driver.

Tested camera family: Anyka AK39EV330 / ARM926EJ-S, Linux 4.4.192V2.1,
firmware bundle HT_IPC286KSD3M_TUYA_AK3918EV330, version 3.2863.105.28.
Other cameras sold under the same brand may use different hardware or firmware.
The camera's vendor app continues to control pan/tilt. LayerSentra does not yet
provide pan/tilt controls, position presets, automatic tracking or auto-calibration.

## Prerequisites

- A camera you own with an **already working, verified SD bootstrap** that invokes
  `/tmp/sd/custom.sh` after the SD is mounted.
- BusyBox for the camera architecture with its HTTP server applet.
- An existing compatible `lsc-reader-armv5-v0.3` executable accepting
  `/tmp/VideoSubStream0 20` and emitting the LSC1 records described below.
- FFmpeg installed on the LayerSentra host, with H.264 decoding and MJPEG encoding.

The vendor firmware, BusyBox executable, camera reader executable, trained model,
flash dumps and camera recordings are **not distributed** here. The original C
source for the pre-existing reader was not available in the recovered installation.
This repository therefore cannot build that component from source. Bring your
own authorized and compatible components; this is an integration for an existing
camera setup, not a complete firmware replacement.

## Prepare the camera SD

1. Back up the existing SD, especially `custom.sh`. Never overwrite a bootstrap
   you do not understand; merge the startup fragment if it already runs services.
2. Copy the **contents** of `camera-sd/` to the root of the SD, after reviewing
   `custom.sh`. It uses `/tmp` for the web root and port 8080; it does not flash
   firmware or change the camera's account database.
3. Generate a strong password locally and create `lsc-web/httpd.conf` on the SD:
   `/:camera:YOUR_GENERATED_PASSWORD`. Keep the same password for the host config.
   Do not commit this file. Usernames/passwords must not contain a colon or newline.
4. Ensure the camera's compatible BusyBox and reader exist at the SD root.
5. Insert the SD while the camera is off. Boot and wait at least 60 seconds.
   Leave the SD installed. The optional `lsc-network-start.txt` records HTTP startup.

The server uses HTTP Basic authentication. It is intended for a trusted local
network, not direct Internet access. Do not forward its port on your router.

## Configure LayerSentra

1. Copy `examples/lsc-camera.example.json` to `data/lsc-camera.json`.
2. Set the camera capture URL, your generated username/password and the absolute
   FFmpeg executable path. Keep this file private (`chmod 600 data/lsc-camera.json`
   on macOS/Linux). Never put credentials in a camera URL.
3. Restart LayerSentra so its bridge thread starts.
4. In the local dashboard's camera settings, enable the second camera and set its
   URL to `http://127.0.0.1:7127/api/lsc/snapshot`.
5. Save and check `http://127.0.0.1:7127/api/lsc/status`. `ready: true` means a
   recent JPEG exists. `/api/frame/secondary` is the processed camera JPEG used
   by the dashboard and can also be displayed in compatible snapshot clients.

The bridge automatically reconnects after each bounded 20-second camera request.
The camera reader includes its current ring buffer at connection time, so output
frame count does not directly measure request duration. The host skips repeated
source timestamps and refuses to serve JPEGs older than eight seconds. Clock
resets larger than one minute begin a new source epoch. Short reset/decoder and
network recovery gaps can occur. This is snapshot monitoring, not continuous video
with audio. Stale or missing frames reset AI evidence in LayerSentra.

## Troubleshooting

| Symptom | Check |
| --- | --- |
| `configured: false` | Place the private config in the application's `data` directory and restart. |
| HTTP 401 | Camera and host credentials must match. |
| HTTP 409 | Another capture owns the camera lock; stop duplicate clients. |
| HTTP 503 / expired image | Check power, Wi-Fi, SD mount, `/tmp/VideoSubStream0`, reader and FFmpeg. |
| Camera works in vendor app only | The vendor cloud video is independent of the SD HTTP service. |
| No AI boxes while idle | AI inference in the monitor runs only during an actual print with fresh printer status. |
| Camera angle changes | Stop/reframe monitoring and check ROI/masks before relying on detections. |

If a capture process is killed abruptly, its lock may remain for the current boot.
The lock is in `/tmp`, so a normal camera reboot clears it. Do not remove a lock
while another capture is active.

## LSC1 wire format

Each record consists of a 16-byte big-endian header (`>4sQI`) followed by a payload:

| Field | Bytes | Meaning |
| --- | ---: | --- |
| magic | 4 | ASCII `LSC1` |
| timestamp | 8 | Source timestamp in milliseconds |
| payload size | 4 | Length of payload, maximum 2 MiB accepted by host |
| payload | variable | One H.264 access unit in Annex B format, with start codes |

The HTTP capture is binary (`application/octet-stream`), not an image or RTSP URL.
