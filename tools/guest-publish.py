"""Publish only the explicitly authorized guest port; keep owner ports private."""
import json
from pathlib import Path
import subprocess
from urllib.parse import urlsplit

cli = '/Applications/Tailscale.app/Contents/MacOS/Tailscale'
root = Path.home() / 'Applications/LayerSentraGuest'
settings = json.loads((root / 'data/guest-access.json').read_text())
network = json.loads(subprocess.check_output([cli, 'status', '--json'], text=True))
hostname = network['Self']['DNSName'].rstrip('.')
assert settings['origin'] == 'https://' + hostname + ':10000'
assert settings['enabled'] is True and settings['expires_at'] is None
before = json.loads(subprocess.check_output([cli, 'serve', 'status', '--json'], text=True))
if '10000' in before.get('TCP', {}):
    raise SystemExit('Porta10000 gia configurata: verificare prima di sostituire.')
subprocess.run([cli, 'funnel', '--bg', '--https=10000', '7130'], check=True)
after = json.loads(subprocess.check_output([cli, 'serve', 'status', '--json'], text=True))
assert after.get('AllowFunnel', {}).get(hostname + ':10000') is True
for address, public in after.get('AllowFunnel', {}).items():
    if address in (hostname + ':443', hostname + ':8443'):
        assert public is not True
print('PUBBLICATO_SOLO_OSPITE:', settings['origin'])
print('Porte proprietarie conservate private. Invito nel file locale riservato.')
