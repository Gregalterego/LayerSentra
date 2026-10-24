#!/bin/zsh
set -eu
cd -- "${0:A:h}"
if [[ ! -x .venv/bin/python ]]; then print 'Eseguire prima install.command'; exit 1; fi
.venv/bin/python - <<'PY'
from pathlib import Path
import os, plistlib, subprocess
root=Path.cwd()
folder=Path.home()/'Library/LaunchAgents'
folder.mkdir(parents=True,exist_ok=True)
file=folder/'local.printwatch.observer.plist'
if file.exists(): raise SystemExit('Esiste già un servizio PrintWatch: verificare la configurazione prima di sostituirlo.')
config={'Label':'local.printwatch.observer','ProgramArguments':[str(root/'.venv/bin/python'),'-m','printwatch.app','--observe'],
        'WorkingDirectory':str(root),'RunAtLoad':True,'KeepAlive':True,'ThrottleInterval':30,
        'StandardOutPath':str(root/'data/service.log'),'StandardErrorPath':str(root/'data/service-error.log'),
        'EnvironmentVariables':{'PATH':'/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin'}}
with file.open('xb') as f: plistlib.dump(config,f)
try: subprocess.run(['launchctl','bootstrap',f'gui/{os.getuid()}',str(file)],check=True)
except subprocess.CalledProcessError:
    raise SystemExit('File salvato, servizio non avviato. Serve una sessione grafica attiva dell’utente; verificare launchctl prima di riprovare.')
print('Avvio automatico attivato al login dell’utente, esclusivamente in osservazione. Non impedisce la sospensione del Mac.')
PY
