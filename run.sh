#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

PYTHON_BIN="/opt/homebrew/bin/python3.14"
if [ ! -x "$PYTHON_BIN" ]; then
  PYTHON_BIN="/usr/bin/python3"
fi

if ! "$PYTHON_BIN" -c "import tkinter" 2>/dev/null; then
  echo "Could not find a Python with tkinter installed."
  echo "Install one with: brew install python-tk@3.14"
  exit 1
fi

if [ ! -d ".venv" ] || [ ! -f ".venv/.python-version" ] || ! grep -q "3.14" ".venv/.python-version" 2>/dev/null; then
  rm -rf .venv
  "$PYTHON_BIN" -m venv .venv
  echo "3.14" > .venv/.python-version
fi

source .venv/bin/activate
pip install -q -r requirements.txt
python main.py
