"""Check the installed guest service without issuing printer commands."""
from pathlib import Path
from http.cookies import SimpleCookie
import io
import json
import subprocess
from urllib.parse import urlsplit
import requests
from PIL import Image

root = Path.home() / 'Applications/LayerSentraGuest'
cfg = json.loads((root / 'data/guest-access.json').read_text())
origin = cfg['origin']
host = urlsplit(origin).netloc
base = 'http://127.0.0.1:7130'
headers = {'Host': host, 'Origin': origin}
anonymous = requests.get(base + '/api/status', headers=headers, timeout=8)
assert anonymous.status_code == 401
token = (root / 'data/invito-riservato.txt').read_text().strip().split('#invite=', 1)[1]
login = requests.post(base + '/session', headers=headers, json={'token': token}, timeout=8)
assert login.status_code == 200
cookie = SimpleCookie()
cookie.load(login.headers['Set-Cookie'])
headers['Cookie'] = '; '.join(k + '=' + v.value for k, v in cookie.items())
response = requests.get(base + '/api/status', headers=headers, timeout=10)
assert response.status_code == 200
status = response.json()
assert 'csrf' in status
for path in ('/api/config', '/api/ptz', '/printer/gcode/script', '/printer/print/resume'):
    assert requests.get(base + path, headers=headers, timeout=8).status_code == 403
frame = requests.get(base + '/api/frame', headers=headers, timeout=10)
assert frame.status_code == 200
with Image.open(io.BytesIO(frame.content)) as image:
    print('VIDEO_VERIFICATO', image.size)
print('ACCESSO_ANONIMO_NEGATO; ALTRI_COMANDI_BLOCCATI; STATO', status['state'])
print('Nessuna pausa o altro comando alla stampante eseguito.')
cli = '/Applications/Tailscale.app/Contents/MacOS/Tailscale'
network = json.loads(subprocess.check_output([cli, 'serve', 'status', '--json'], text=True))
print('PORTE_TAILSCALE_CONFIGURATE', sorted(network.get('TCP', {}).keys()))
print('Servizio ospite in ascolto solo su 127.0.0.1:7130.')
