#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

if ! command -v ffmpeg >/dev/null 2>&1; then
  echo "ffmpeg não encontrado. Instale com: brew install ffmpeg"
  exit 1
fi

pick_python() {
  if [[ -x /opt/homebrew/opt/python@3.12/bin/python3.12 ]]; then
    echo /opt/homebrew/opt/python@3.12/bin/python3.12
  elif command -v python3.12 >/dev/null 2>&1; then
    command -v python3.12
  else
    command -v python3
  fi
}

if [[ ! -d .venv ]]; then
  PY="$(pick_python)"
  "$PY" -m venv .venv
fi

# shellcheck disable=SC1091
source .venv/bin/activate
pip install -q -r requirements.txt
exec python app.py
