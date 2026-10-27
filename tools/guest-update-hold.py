"""Update only the guest service after explicit dual-camera/resume authorization."""
import argparse
from http.cookies import SimpleCookie
import json
import os
from pathlib import Path
import shutil
import subprocess
import time
import urllib.request
import requests

parser = argparse.ArgumentParser()
parser.add_argument('--enable-resume', action='store_true', required=True,
                    help='Confirm owner authorization for guest resume and both cameras')
parser.parse_args()
root = Path.home() / 'Applications/LayerSentraGuest'
settings = root / 'data/guest-access.json'
cfg = json.loads(settings.read_text())
revision = 'd3e77c30fd8078b8a0462aa581b667034e6ac881'
base = 'https://raw.githubusercontent.com/Gregalterego/LayerSentra/' + revision + '/'
files = ['layersentra/guest.py', 'layersentra/io.py', 'guest/index.html',
         'guest/guest.css', 'guest/guest.js']
stamp = str(time.time_ns())
staging = root / ('update-hold-' + stamp)
staging.mkdir(mode=0o700)
backup = root / 'data' / ('backup-before-hold-' + stamp)
backup.mkdir(mode=0o700)
for relative in files:
    target = staging / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(base + relative, timeout=30) as response:
        code = response.read()
    if target.suffix == '.py':
        compile(code, relative, 'exec')
    target.write_bytes(code)
    previous = backup / relative
    previous.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(root / relative, previous)
shutil.copy2(settings, backup / 'guest-access.json')
(backup / 'guest-access.json').chmod(0o600)
cfg['camera_ids'] = ['primary', 'secondary']
cfg['can_resume'] = True
agent = Path.home() / 'Library/LaunchAgents/local.layersentra.guest.plist'
domain = 'gui/' + str(os.getuid())
subprocess.run(['launchctl', 'bootout', domain, str(agent)], check=True)
try:
    for relative in files:
        os.replace(staging / relative, root / relative)
    temporary = settings.with_suffix('.hold-update.json')
    temporary.write_text(json.dumps(cfg))
    temporary.chmod(0o600)
    os.replace(temporary, settings)
    subprocess.run(['launchctl', 'bootstrap', domain, str(agent)], check=True)
    headers = {'Host': cfg['origin'].split('//', 1)[1], 'Origin': cfg['origin']}
    local = 'http://127.0.0.1:7130'
    for _ in range(20):
        try:
            response = requests.get(local + '/', headers=headers, timeout=2)
            if response.status_code == 200:
                break
        except requests.RequestException:
            pass
        time.sleep(0.5)
    else:
        raise RuntimeError('Servizio ospite non pronto')
    invite = (root / 'data/invito-riservato.txt').read_text().strip().split('#invite=', 1)[1]
    response = requests.post(local + '/session', headers=headers,
                             json={'token': invite}, timeout=8)
    response.raise_for_status()
    cookie = SimpleCookie()
    cookie.load(response.headers['Set-Cookie'])
    headers['Cookie'] = '; '.join(k + '=' + v.value for k, v in cookie.items())
    result = requests.get(local + '/api/status', headers=headers, timeout=10)
    result.raise_for_status()
    status = result.json()
    assert status['hold_seconds'] == 5 and status['can_resume'] is True
    assert [c['id'] for c in status['cameras']] == ['primary', 'secondary']
    headers['X-Guest-CSRF'] = status['csrf']
    # Mint and cancel a hold; never send pause or resume to the printer.
    response = requests.post(local + '/api/hold', headers=headers,
                             json={'action': 'resume'}, timeout=8)
    response.raise_for_status()
    cancelled = requests.post(local + '/api/hold/cancel', headers=headers,
                               json={'hold_token': response.json()['hold_token']}, timeout=8)
    cancelled.raise_for_status()
    for cid in ('primary', 'secondary'):
        frame = requests.get(local + '/api/frame/' + cid, headers=headers, timeout=10)
        print('CAMERA', cid, 'HTTP', frame.status_code)
    print('AGGIORNATO: due camere, pausa e ripresa a pressione continua di cinque secondi.')
    print('Invito e accesso Internet invariati. Nessuna pausa o ripresa reale eseguita.')
except Exception:
    subprocess.run(['launchctl', 'bootout', domain, str(agent)], check=False)
    for relative in files:
        shutil.copy2(backup / relative, root / relative)
    shutil.copy2(backup / 'guest-access.json', settings)
    subprocess.run(['launchctl', 'bootstrap', domain, str(agent)], check=False)
    raise
