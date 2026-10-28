#!/bin/zsh
set -eu
cd -- "${0:A:h}"
PYTHON_BIN=${LAYERSCAN_PYTHON:-${PRINTWATCH_PYTHON:-}}
if [[ -z "$PYTHON_BIN" ]]; then
 for candidate in /opt/homebrew/bin/python3.12 /usr/local/bin/python3.12 /Library/Frameworks/Python.framework/Versions/3.12/bin/python3.12; do
  if [[ -x "$candidate" ]]; then PYTHON_BIN="$candidate"; break; fi
 done
fi
if [[ -z "$PYTHON_BIN" || ! -x "$PYTHON_BIN" ]]; then
 print 'Serve Python 3.12. Installarlo prima o impostare LAYERSCAN_PYTHON al suo percorso.'
 exit 1
fi
"$PYTHON_BIN" -m venv .venv
if [[ "$(uname -m)" == arm64 ]]; then
 .venv/bin/python -m pip install -r requirements.lock.txt
else
 .venv/bin/python -m pip install -r requirements-intel.txt
fi
print 'Ambiente pronto. Apri start.command e visita http://127.0.0.1:7127'
