# PrintWatch

Local AI print monitoring for Klipper printers, with a large camera view, a full
Fluidd/Mainsail control panel, and filament accounting. Runs on your own computer.
No AI cloud service, subscription or demo timer is required by PrintWatch.

[Guida in italiano](README.it.md) · [Own server / domain](HOSTING.md) · [MIT license](LICENSE)

## What it does

- Large camera view with full-screen mode and optional AI bounding boxes.
- A compact view that can be added to Fluidd's **Cameras** section: image first,
  small status/buttons, detailed metrics and filament information on demand.
- Class-specific thresholds and area filters for spaghetti, blobs, warping and cracks.
- Separate temporal confirmation for each camera/class. Clean or missing frames
  reset evidence; low-confidence guesses are not treated as confirmed failures.
- Per-camera region of interest and exclusion masks, configured as normalized rectangles.
- Full existing Fluidd/Mainsail UI through a private local proxy, including WebSockets.
- Filament sensor status, reported print consumption, slicer-based material needed,
  manually initialized spool accounting and estimated remaining runtime.
- SQLite event history, JSON export and labelled-frame evaluation tooling.
- Optional private Tailscale access. The AI dashboard is read-only remotely;
  the separate printer UI provides real printer controls to the configured owner.

**A trained AI model is not included.** Bring a compatible model you are authorized
to use. See [model requirements and provenance](models/README.md). No improved
accuracy, reliable failure prevention or new model training is claimed.

## Requirements and tested scope

- Python **3.12**, a Klipper printer with reachable Moonraker, and an HTTP snapshot camera.
- AI runtime: LiteRT on supported platforms; TensorFlow 2.16.2 for Intel macOS.
- RTSP capture additionally needs FFmpeg in PATH. App invitation URLs are not video streams.
- The application must remain running and the host must stay awake.

A working Apple Silicon macOS installation and a live Klipper/Fluidd connection
have been exercised. Intel macOS installation requirements are provided, but have
not been verified on an actual Intel machine. Linux/Windows need compatible Python
wheels and have not yet been tested end to end. Local development uses HTTP loopback
only; private phone access uses Tailscale Serve HTTPS. External service terms apply.

## Install and run

Clone or download this repository. In its directory:

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.lock.txt
.venv/bin/python -m printwatch.app
```

On Intel macOS, use `requirements-intel.txt` instead of `requirements.lock.txt`.
On Windows, activate the virtual environment and use `python` with these same
module commands (the interpreter is `.venv\Scripts\python.exe`).

macOS users can also use `install.command`, then `start.command`, if Python 3.12
is already installed. The installer does not install Python or request admin access.

Open **http://127.0.0.1:7127**. In **Parametri**:

1. Set the base Moonraker/printer address reachable from this computer.
2. Set an enabled camera to a single-image HTTP/HTTPS snapshot URL.
3. Add your compatible model to `models/model.tflite` and restart if needed.
4. Start observation during a print. Validate detections on your own setup.

Defaults use loopback placeholders, not anyone's printer address. No printer
services, firmware or macros are modified by installation. Printer UI commands,
if used, act on the real machine.

At normal startup, monitoring and automatic pause are disabled. Use
`python -m printwatch.app --observe` to start observation explicitly; it always
forces observe-only mode. Automatic pause is optional, requires temporal confirmation
and checks the printer state. Real pause operation is not part of the public tests.

## Optional LSC / Anyka camera

An optional local bridge converts a compatible camera’s LSC1/H.264 stream into
fresh JPEG snapshots. The second camera uses the same AI, ROI, masks and temporal
confirmation pipeline as the main camera. See the [camera setup guide](docs/LSC-CAMERA.md).
Pan/tilt remains controlled by the vendor app; camera binaries are not bundled.

## Printer UI and camera embedding

Click **Pannello Klipper completo** to open the printer's own UI. The local proxy
is **http://127.0.0.1:7128**. For camera embedding, add a **HTTP page / iframe** camera
in Fluidd with a client-reachable URL for PrintWatch and the query `?embed=camera`.
Use your private HTTPS address for phones. Do not use `127.0.0.1` unless the browser
runs on the same computer as PrintWatch.

The compact layout puts the camera first and opens details via **Dati e filamento**.
The proxy corrects the width of this iframe in older Fluidd layouts; it does not
change the printer's web files. A native camera tile in a phone app may not support
HTML pages: `/api/frame/primary` supplies a JPEG snapshot instead, not an MJPEG stream.

## Filament: measured status versus estimated quantity

Klipper's presence/motion sensors cannot tell how many grams are left. Disabled
sensors are clearly shown as disabled; PrintWatch never enables them automatically.

On the local dashboard, **Imposta bobina** records the material weight available
*now*, excluding the empty spool. Subsequent reported consumption is subtracted
using configured diameter and material density. Slicer metadata estimates how much
material is needed to finish. Low/insufficient spool warnings are displayed.
Estimated runtime needs at least 30 seconds of observed printing, using up to five
minutes of consumption history. It is not a physical scale or guaranteed ETA.

Manual extrusion, unrecorded spool changes and prints completed while PrintWatch
was off can invalidate the estimate. Re-enter a known remaining weight. These
warnings do not trigger push notifications or automatically pause a print.

## Private phone access (optional)

Install Tailscale and sign in on both the host and phone. Then run:

```sh
.venv/bin/python -m printwatch.remote_setup --enable-serve
```

This derives the current computer's name and owner from Tailscale, writes a local
identity file excluded from Git, and requests Serve on HTTPS ports 443 and 8443.
Tailscale may ask you to enable Serve/HTTPS in its account UI. Existing Serve rules
must be reviewed for port conflicts before using this command. Public Funnel is not used.
Restart PrintWatch after setup. The command prints your own private URLs.

The AI view is remote read-only. Port 8443 is the full printer control panel and
allows real printer actions; the proxy requires the configured owner identity.
Keep the backend bound to loopback. No credentials need to be committed to Git.

## Tests and evaluation

```sh
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -m printwatch.evaluate dataset/manifest.json --output data/report.json
```

The tests exercise confirmation isolation, missing frames, pause gating, class-aware
NMS, coordinate mapping, private proxy access, spool accounting and evaluation math.
They do not prove accuracy on actual print defects. Labelled frames are required:

```json
[
  {"image":"normal.jpg","annotations":[]},
  {"image":"failure.jpg","annotations":[{"category":"spaghetti","box":[0.2,0.3,0.25,0.2]}]}
]
```

Paths are relative to the manifest; boxes are `[x,y,width,height]` in 0–1 coordinates.
The report uses same-class IoU >= 0.5 matching for per-frame precision/recall, not mAP
or false alarms/hour. Labels must match the configured ROI and masks.

## Local data and limits

Runtime files live in `data/` and are ignored by Git: configuration, private identity,
spool counters, events and logs. Models are ignored too. No real printer images,
private network settings or credentials are shipped.

The default language of the UI is Italian. Current model adapter assumes four
specific classes; custom training is not implemented. Confirmation is by class/camera,
not object tracking. Identical frames can indicate a frozen camera but do not prove
it. There is no push notification service. Current UI is served by Flask's local
server, not a public Internet deployment. Keep automatic actions disabled until
validated on representative normal and failed prints.

`enable-autostart.command` can create a macOS user LaunchAgent in observe-only mode.
It needs an active user session, does not bypass FileVault/login, and does not prevent
sleep. No remote access or startup service is enabled just by downloading the repository.

## Continuous operation and laptop sleep

PrintWatch cannot monitor while its host computer is asleep or off. Tailscale does
not change that. For a permanent installation, deploy on an always-awake desktop
or other suitable host and test service startup and phone access on that host.
See [continuous deployment checklist](DEPLOYMENT.md) before relying on unattended monitoring.

## Host it on your own server

Use an always-on desktop, local Linux server or a VPS with private access to the
printer. The [hosting guide](HOSTING.md) includes an authenticated Caddy HTTPS
configuration generator, a systemd service and deployment checks. The public
repository contains no user configuration, host identities, trained models or logs.
