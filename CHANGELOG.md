# Changelog

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
