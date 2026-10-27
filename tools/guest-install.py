"""Install a separate loopback-only guest service. Does not enable public access."""
import hashlib
import json
import os
from pathlib import Path
import plistlib
import secrets
import socket
import subprocess
import sys
import time
import urllib.request


def main():
    home = Path.home()
    owner = home / 'Applications/PrintWatch'
    if not (owner / 'data/config.json').is_file():
        owner = home / 'Applications/LayerSentra'
    source_config = owner / 'data/config.json'
    if not source_config.is_file():
        raise SystemExit('Configurazione del server proprietario non trovata.')
    target = home / 'Applications/LayerSentraGuest'
    agent = home / 'Library/LaunchAgents/local.layersentra.guest.plist'
    if target.exists() or agent.exists():
        raise SystemExit('Installazione ospite gia presente: verificare prima di aggiornare.')
    with socket.socket() as sock:
        if sock.connect_ex(('127.0.0.1', 7130)) == 0:
            raise SystemExit('Porta ospite gia occupata: nessuna modifica.')
    with urllib.request.urlopen('http://127.0.0.1:7127/api/status', timeout=8) as r:
        status = json.load(r)
    cameras = status.get('cameras', {})
    camera = next((cid for cid in ('secondary', 'primary')
                   if cameras.get(cid, {}).get('state') == 'ok'), None)
    if camera is None:
        raise SystemExit('Nessuna telecamera disponibile: nessuna installazione.')
    cli = Path('/Applications/Tailscale.app/Contents/MacOS/Tailscale')
    network = json.loads(subprocess.check_output([str(cli), 'status', '--json'], text=True))
    hostname = network['Self']['DNSName'].rstrip('.')
    if not hostname.endswith('.ts.net'):
        raise SystemExit('Nome HTTPS Tailscale non valido: non pubblicare.')
    origin = 'https://' + hostname + ':10000'
    # Fetch only known source files at an immutable, reviewed commit.
    revision = '12b48f067dfb7d8105674d1153c810cf178aa073'
    base = 'https://raw.githubusercontent.com/Gregalterego/LayerSentra/' + revision + '/'
    files = ['layersentra/__init__.py', 'layersentra/guest.py', 'layersentra/config.py',
             'layersentra/io.py', 'guest/index.html', 'guest/guest.js', 'guest/guest.css']
    target.mkdir(parents=True, mode=0o700)
    for relative in files:
        path = target / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        with urllib.request.urlopen(base + relative, timeout=30) as response:
            path.write_bytes(response.read())
    data = target / 'data'
    data.mkdir(mode=0o700)
    (data / 'config.json').write_bytes(source_config.read_bytes())
    (data / 'config.json').chmod(0o600)
    token = secrets.token_urlsafe(32)
    settings = dict(origin=origin, camera_id=camera, enabled=True,
                    expires_at=time.time() + 7 * 24 * 3600,
                    token_hash=hashlib.sha256(token.encode()).hexdigest(),
                    session_key=secrets.token_urlsafe(48))
    (data / 'guest-access.json').write_text(json.dumps(settings))
    (data / 'guest-access.json').chmod(0o600)
    invitation = data / 'invito-riservato.txt'
    invitation.write_text(origin + '/#invite=' + token + '\n')
    invitation.chmod(0o600)
    subprocess.run([sys.executable, '-m', 'venv', str(target / '.venv')], check=True)
    python = target / '.venv/bin/python'
    subprocess.run([str(python), '-m', 'pip', 'install', '--disable-pip-version-check',
                    'Flask>=3.1,<4', 'requests>=2.32,<3', 'Pillow>=11,<14',
                    'waitress>=3,<4'], check=True)
    runner = target / 'run_guest.py'
    runner.write_text("from waitress import serve\nfrom layersentra.guest import create_app\n"
                      "serve(create_app(), host='127.0.0.1', port=7130, threads=4)\n")
    agent.parent.mkdir(parents=True, exist_ok=True)
    payload = dict(Label='local.layersentra.guest',
                   ProgramArguments=[str(python), str(runner)],
                   WorkingDirectory=str(target), RunAtLoad=True, KeepAlive=True,
                   StandardOutPath=str(data / 'guest.log'),
                   StandardErrorPath=str(data / 'guest-error.log'))
    agent.write_bytes(plistlib.dumps(payload))
    agent.chmod(0o600)
    subprocess.run(['launchctl', 'bootstrap', 'gui/' + str(os.getuid()), str(agent)], check=True)
    for _ in range(20):
        try:
            req = urllib.request.Request('http://127.0.0.1:7130/',
                                         headers={'Host': hostname + ':10000'})
            with urllib.request.urlopen(req, timeout=2) as r:
                assert b'PAUSA STAMPA' in r.read()
            break
        except (OSError, AssertionError):
            time.sleep(0.5)
    else:
        raise SystemExit('Servizio preparato ma verifica locale fallita: non pubblicare.')
    print('OSPITE_INSTALLATO_LOCALE: video e PAUSA STAMPA. Nessun comando alla stampante.')
    print('Accesso Internet NON attivato. I servizi proprietari non sono stati modificati.')
    print('Invito riservato salvato nel file: ' + str(invitation))


if __name__ == '__main__':
    main()
