#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."

echo "[bootstrap] Ensuring Python venv and backend dependencies..."

# Create venv if missing
if [ ! -d .venv ]; then
  echo "[bootstrap] Creating .venv"
  python3 -m venv .venv
fi

# Upgrade pip and install requirements
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r backend/requirements.txt

echo "[bootstrap] Done"
