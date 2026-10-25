# Security and deployment boundaries

PrintWatch is a local prototype, not an Internet-facing printer management service.
Its dashboard binds to loopback on port 7127 and its full-UI proxy to loopback on 7128.
Do not change these to 0.0.0.0 or expose them with router port forwarding.

Optional private access relies on Tailscale Serve, owner identity headers and the
configured hostname. Another program on the same host can spoof loopback requests;
this is not isolation from a compromised user account. Do not commit data/mobile-access.json,
tokens, camera credentials or printer configuration. URLs containing usernames/passwords
are rejected by the configuration validator.

The full printer UI can move hardware, heat tools, run macros and modify files. It
is intentionally a control surface, unlike the remote read-only AI dashboard.
Klipper/Moonraker and the printer UI retain their own behavior and vulnerabilities.

Filament estimates and AI scores must not be treated as safety guarantees. Model
accuracy is not established by passing software tests. Automatic pause defaults off.

When reporting a security issue, provide a sanitized reproduction without secrets,
private URLs, full camera images or personally identifying logs. Avoid public details
that enable abuse of an unpatched installation.

## Personal-domain deployments

The optional self-host generator requires a same-machine Caddy proxy, HTTPS and
Basic Authentication on both ports. A random upstream secret is checked with
constant-time comparison, together with loopback source and exact Host. The
proxy overwrites client-supplied identity headers and strips user credentials.
Generated files in data/ are private: never commit them. Remote dashboard writes
remain forbidden; the separate gateway grants actual printer controls.
Keep 7127/7128 inaccessible from the network. Do not forward arbitrary requests
with a localhost Host to these services or bypass the proxy authentication.

### Remote controls in server 0.3.0

The remote dashboard now permits only scoped observation start/stop and, when
explicitly configured, PTZ pulse commands. These use separate tokens and the same
remote authentication/origin checks. General configuration changes remain denied.
Starting or stopping observation always forces observe-only mode.
