#!/bin/zsh
set -eu
cd -- "${0:A:h}"
# Run from the newly downloaded source on the host that already runs LayerSentra.
TARGET="${LAYERSENTRA_HOME:-$HOME/Applications/LayerSentra}"
if [[ ! -x "$TARGET/.venv/bin/python" && -z "${LAYERSENTRA_HOME:-}" && -x "$HOME/Applications/PrintWatch/.venv/bin/python" ]]; then
 TARGET="$HOME/Applications/PrintWatch"
fi
if [[ "$PWD" == "$TARGET" ]]; then
 print 'Estrai la nuova versione in una cartella separata prima di aggiornare.'; exit 1
fi
if [[ ! -x "$TARGET/.venv/bin/python" ]]; then
 print 'Installazione precedente non trovata in ~/Applications/LayerSentra.'; exit 1
fi
"$TARGET/.venv/bin/python" - "$PWD" "$TARGET" <<'PY'
from pathlib import Path
import datetime, os, shutil, subprocess, sys
import requests
source,target=map(Path,sys.argv[1:])
import plistlib
units=[]
for label in ('local.layersentra.observer','local.printwatch.observer'):
 candidate=Path.home()/'Library/LaunchAgents'/(label+'.plist')
 if candidate.exists():
  with candidate.open('rb') as file: config=plistlib.load(file)
  if Path(config.get('WorkingDirectory','')).resolve()==target.resolve():units.append(candidate)
if len(units)!=1:raise SystemExit('Serve un solo servizio personale associato alla cartella scelta.')
unit=units[0]
if not (source/'layersentra/ptz.py').exists():raise SystemExit('Sorgenti incompleti.')
try:
 status=requests.get('http://127.0.0.1:7127/api/status',timeout=5).json()
 if status.get('printer',{}).get('state') in ('printing','paused'):
  raise SystemExit('Termina la stampa prima di aggiornare il monitor.')
except requests.RequestException:
 raise SystemExit('Il servizio locale deve essere raggiungibile per verificare lo stato prima di aggiornare.')
backup=target/'data/backups'/datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f')
backup.mkdir(parents=True,mode=0o700)
folders=('layersentra','printwatch','static')
for name in folders:
 if (target/name).exists():shutil.copytree(target/name,backup/name,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
domain='gui/'+str(os.getuid())
subprocess.run(['launchctl','bootout',domain,str(unit)],check=True)
try:
 for name in folders:shutil.copytree(source/name,target/name,dirs_exist_ok=True,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
 subprocess.run([str(target/'.venv/bin/python'),'-m','compileall','-q',str(target/'layersentra')],check=True)
 subprocess.run(['launchctl','bootstrap',domain,str(unit)],check=True)
except Exception:
 for name in folders:
  if (backup/name).exists():shutil.copytree(backup/name,target/name,dirs_exist_ok=True)
 subprocess.run(['launchctl','bootstrap',domain,str(unit)],check=False)
 raise
print('LayerSentra aggiornato. Backup:',backup)
print('Il percorso e il servizio precedenti vengono conservati per la compatibilità.')
print('Modello, configurazione, identità remota e storico conservati.')
print('Ricarica il pannello: Avvia/Ferma analisi AI è disponibile anche da remoto.')
print('Il movimento LSC rimane disabilitato senza un bridge PTZ verificato.')
PY
