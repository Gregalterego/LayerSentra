# Running LayerSentra continuously

## A reachable URL is not a running server

Tailscale Serve forwards traffic; it does not run the AI application, wake a sleeping
computer or replace the computer hosting LayerSentra. If that computer sleeps,
shuts down, loses its printer route or exits the application, remote monitoring stops.
Closing a laptop lid normally makes it unsuitable as an unattended host.

Use a computer that can stay powered, awake and connected to both printer and clients.
The host does not need a lit display. Prefer a stable printer address, for example
a DHCP reservation in the router. An address reservation alone does not start any service.

## macOS desktop deployment

1. Install Python 3.12 and LayerSentra on the destination computer, not on a different laptop.
2. Set the destination's own printer and camera addresses in the local dashboard.
3. Add a compatible model with appropriate usage rights and verify live observation.
4. The startup helper uses `caffeinate -s` to prevent system sleep while on mains
   power, while permitting display sleep. Verify the actual behavior on the host.
5. Run `enable-autostart.command` only after checking that another copy is not running.
   It installs a user LaunchAgent and starts observe-only monitoring after that user logs in.
6. For remote access, configure Tailscale on the destination and run
   `python -m layersentra.remote_setup --enable-serve`. The printed destination URLs
   are different from the laptop's URLs. Update any camera embedding or phone shortcut.
7. Stop the old installation when the new one has been tested, to avoid duplicate monitoring.

The startup helper does not configure automatic OS login, bypass FileVault, unlock
the computer after a power loss, or change global power settings. Its sleep assertion
lasts while the service is running and does not prevent manual shutdown. A user login/unlock can
still be necessary following a reboot. Those limits must be tested before relying
on unattended restart.

## Transfer and remote installation

Download the public source on the destination or use an authorized SSH connection.
On macOS, Remote Login is an OS sharing setting; enable it only for the intended user.
Never put passwords, SSH private keys or Tailscale identity files in the repository.
Do not copy the source host's `mobile-access.json`: generate it on the destination.

If moving an existing installation, copy private configuration, spool state and models
only over a private channel, with the appropriate permissions. Keep a backup, review
printer routes, and regenerate the host identity. Do not publish that data.

## Acceptance checks

- Printer status and camera frames update on the destination.
- AI model is ready and observation works on a known frame.
- Phone access works over Tailscale with Wi-Fi disabled on the phone.
- Access still works after the host display has turned off.
- The service returns after logout/login or reboot as intended, accounting for OS unlock.
- The camera link inside Fluidd points to the destination host.
- Automatic actions remain disabled until independently validated.

Passing unit tests does not establish these deployment properties. A local user
LaunchAgent is a convenience for desktop sessions, not a high-availability service.

## Own server or domain

See [HOSTING.md](HOSTING.md) or [the detailed Italian guide](HOSTING.it.md) for
Linux systemd, a VPS with a VPN route, and authenticated HTTPS on a personal domain.
A domain or static hosting link cannot replace an application server.

## Exercised desktop migration

An Apple Silicon desktop installation was checked with Python 3.12.15, live model
inference and a working Klipper/Fluidd connection. The previous laptop process was
stopped; the desktop dashboard, fresh snapshots, Moonraker API and WebSocket
continued working while the desktop display was asleep. A complete desktop reboot
and arbitrary Linux/cloud deployments have not been verified end to end.
