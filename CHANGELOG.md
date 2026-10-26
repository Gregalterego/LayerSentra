# Changelog

## 0.5.0 — 2026-10-26

- PrintWatch Dot visual identity across the web dashboard and all native clients.
- Shared charcoal/grey/warm-white palette, high-contrast red actions and an original
  dotted wordmark; original launcher icons for all four platforms.
- Camera-first web layout and compact embedded controls with visible AI/details buttons.
- Local, read-only design preview using synthetic data. No external font or brand assets.
- Existing authentication, AI observation and PTZ capabilities are unchanged.


## 0.4.0 — 2026-10-25

- Native Flutter companion source for iOS, Android, macOS and Windows.
- Authenticated, scoped remote start/stop of AI observation, always forcing observe mode.
- AI button is visible remotely and in the compact embedded camera bar.
- Optional directional camera controls, disabled without an explicitly configured,
  bounded-pulse PTZ bridge. No direct LSC PTZ compatibility is claimed.
- macOS code update helper with backup, preserving models, local settings and history.
- Native app build workflow and authorization/PTZ regression tests.

## 0.3.0 — 2026-10-25

- Added optional LSC1/H.264 to JPEG conversion using local FFmpeg.
- Enabled compatible LSC cameras to use the existing multi-camera AI pipeline.
- Added local bridge health and snapshot endpoints, source timestamp deduplication,
  bounded parser inputs, reconnection and stale-image rejection.
- Added camera setup documentation, sample configuration and SD startup/CGI source.
- Added parser/freshness tests and a GitHub Actions unit-test workflow.
- Prepared a source-only distribution excluding local settings, identities,
  credentials, model weights, camera executables, firmware dumps and recordings.

The camera bridge was exercised on macOS Apple Silicon with compatible Anyka
hardware. This release does not claim validated failure-detection accuracy or
unattended automatic-pause reliability.



## 0.2.0 — 2026-10-25

- Add personal-domain hosting with a private Caddy configuration generator.
  Both the dashboard and printer gateway require proxy authentication; remote
  dashboard writes remain disabled. Generated secrets stay in ignored local data.
- Add a reviewed Linux systemd example and Italian/English hosting guides, covering
  VPN access to a remote printer, DNS, HTTPS, phone app constraints and startup checks.
- Prevent idle system sleep on powered macOS hosts while the login service runs,
  allowing display sleep through `caffeinate -s`.
- Record tested desktop migration behavior and clarify user-login/reboot limits.
- Use server-neutral connection messages.
- Add five security/setup tests: 44 unit tests total. Validate a generated Caddyfile
  using official Caddy 2.11.7. Public-domain deployment on an arbitrary server has
  not been exercised end to end.

No trained model, private host configuration, user images or logs are included.
No improvement in model accuracy or automatic safety guarantee is claimed.

## 0.1.0

Initial experimental public release: local monitoring, compact camera view,
filament accounting, Klipper gateway and optional private Tailscale access.
