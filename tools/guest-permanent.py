"""Apply an explicitly authorized permanent invitation to an existing guest service."""
import json
import os
from pathlib import Path
import subprocess
import time
import urllib.request

root = Path.home() / 'Applications/LayerSentraGuest'
settings = root / 'data/guest-access.json'
cfg = json.loads(settings.read_text())
revision = '0dd2ee28ddd3fa08941c8b44cf1da1f764d2380b'
url = 'https://raw.githubusercontent.com/Gregalterego/LayerSentra/' + revision + '/layersentra/guest.py'
with urllib.request.urlopen(url, timeout=30) as response:
    code = response.read()
compile(code, 'guest.py', 'exec')
module = root / 'layersentra/guest.py'
backup = module.with_suffix('.before-permanent.py')
if not backup.exists():
    backup.write_bytes(module.read_bytes())
module.write_bytes(code)
previous = settings.with_suffix('.before-permanent.json')
if not previous.exists():
    previous.write_bytes(settings.read_bytes())
    previous.chmod(0o600)
cfg['expires_at'] = None
temporary = settings.with_suffix('.pending.json')
temporary.write_text(json.dumps(cfg))
temporary.chmod(0o600)
os.replace(temporary, settings)
subprocess.run(['launchctl', 'kickstart', '-k',
                'gui/' + str(os.getuid()) + '/local.layersentra.guest'], check=True)
for _ in range(20):
    try:
        req = urllib.request.Request('http://127.0.0.1:7130/',
                                     headers={'Host': cfg['origin'].split('//', 1)[1]})
        with urllib.request.urlopen(req, timeout=2) as response:
            assert b'PAUSA STAMPA' in response.read()
        break
    except (OSError, AssertionError):
        time.sleep(0.5)
else:
    raise SystemExit('Verifica ospite fallita: non pubblicare.')
print('INVITO_SENZA_SCADENZA_AUTOMATICA: revocabile. Sessioni limitate a otto ore.')
print('Riavviato solo il servizio ospite; nessun comando alla stampante.')
