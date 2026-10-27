#!/bin/zsh
set -eu
cd -- "${0:A:h}"
if [[ ! -x .venv/bin/python ]]; then
  print 'Esegui prima install.command per preparare l’ambiente.'
  exit 1
fi
exec .venv/bin/python -m layersentra.app
