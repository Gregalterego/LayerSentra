"""Configure private Tailscale access for the account running this command."""
import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from .config import ROOT

def main():
    parser=argparse.ArgumentParser(description='Configure owner-only Tailscale access. No public Funnel.')
    parser.add_argument('--enable-serve',action='store_true',help='Also enable private HTTPS 443 (AI view) and 8443 (printer controls)')
    args=parser.parse_args()
    binary=shutil.which('tailscale')
    mac=Path('/Applications/Tailscale.app/Contents/MacOS/Tailscale')
    if not binary and mac.exists(): binary=str(mac)
    if not binary: raise SystemExit('Install and sign in to Tailscale first.')
    result=subprocess.run([binary,'status','--json'],capture_output=True,text=True,check=True)
    state=json.loads(result.stdout)
    if state.get('BackendState')!='Running': raise SystemExit('Tailscale is not connected.')
    node=state['Self']; users=state.get('User',{})
    user=users.get(str(node.get('UserID')),{})
    hostname=node.get('DNSName','').rstrip('.'); login=user.get('LoginName')
    if not hostname or not login: raise SystemExit('Could not resolve the current node owner. No settings written.')
    path=ROOT/'data/mobile-access.json';path.parent.mkdir(exist_ok=True)
    if path.exists(): raise SystemExit('mobile-access.json already exists. Review it rather than overwriting it.')
    with path.open('x') as file: json.dump({'hostname':hostname,'login':login},file,indent=2)
    os.chmod(path,0o600)
    print('Owner-only identity settings saved locally (excluded from Git). Restart LayerSentra to load them.')
    if args.enable_serve:
        for port,target in [('443','7127'),('8443','7128')]:
            subprocess.run([binary,'serve','--bg','--https='+port,'http://127.0.0.1:'+target],check=True)
    print('AI view: https://'+hostname+'/')
    print('Full printer controls: https://'+hostname+':8443/')
    print('Both the host computer and the phone must remain connected to the same Tailscale account.')

if __name__=='__main__': main()
