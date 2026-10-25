# Your own server and domain

[Full step-by-step guide in Italian](HOSTING.it.md)

A personal server, always-on desktop or VPS can run PrintWatch. A domain or link
only names the service: static hosting such as GitHub Pages cannot execute the
Python worker, AI model and WebSocket gateway. A remote server needs a private VPN
route to both Moonraker and the camera. Never expose those devices directly.

1. Install Python 3.12 and the project as described in the README. Add a compatible,
   authorized model. Configure the printer and camera addresses from the server's
   perspective using localhost or an SSH port-forward. Verify local observation.
2. For private access, use `python -m printwatch.remote_setup --enable-serve`.
3. Alternatively, install Caddy 2.8+ on the **same machine** and configure a DNS
   hostname with ports 80/443 and 8443 reachable. Keep 7127/7128 on loopback.
4. Generate private settings and an authenticated HTTPS Caddyfile:

```sh
.venv/bin/python -m printwatch.self_host_setup \
  --hostname watch.example.org --user operator \
  --password-hash "$(caddy hash-password)"
caddy validate --config data/Caddyfile --adapter caddyfile
```

Install the generated `data/Caddyfile` into your Caddy service configuration, or
merge its site blocks if you already host other sites. Restart PrintWatch. The
generator refuses to overwrite an existing remote identity or generated Caddyfile.
Do not share generated files; both are private and excluded from Git.

The HTTPS dashboard on port 443 is read-only. The HTTPS printer gateway on 8443
allows real printer controls. Both require HTTP Basic Authentication. Authenticate
to the 8443 site in a separate tab before embedding it. Phone apps must support
HTTPS, custom ports and Basic Auth; otherwise use the browser or private Tailscale.
Caddy overwrites the upstream secret header and removes user credentials. Only
loopback requests with the expected host and secret are accepted by PrintWatch.
A proxy on a separate host/container is outside this supported topology.

An example Linux systemd unit is included at [deploy/printwatch.service](deploy/printwatch.service).
It assumes `/opt/printwatch`, a dedicated `printwatch` user/group and a prepared
virtual environment. Create the account and set ownership first; the service must
read code/models and write `data/`. Review paths before installing:

```sh
sudo install -m 644 deploy/printwatch.service /etc/systemd/system/printwatch.service
sudo systemctl daemon-reload
sudo systemctl enable --now printwatch
sudo systemctl status printwatch
```

On macOS, the login helper now wraps PrintWatch in `caffeinate -s`: the display can
sleep while the powered system stays awake. A user login may still be required
after reboot. A laptop with its lid closed is not a verified unattended host.

Validate authentication on both sites, fresh camera frames, real inference,
WebSockets, display sleep, old-server shutdown and recovery after reboot. Deployment
on an arbitrary VPS/provider has not been tested end to end. Provider fees and
network traffic are independent of this free software.

References: [Caddy authentication](https://caddyserver.com/docs/caddyfile/directives/basic_auth),
[Caddy reverse proxy](https://caddyserver.com/docs/caddyfile/directives/reverse_proxy),
[systemd services](https://www.freedesktop.org/software/systemd/man/latest/systemd.service.html).
