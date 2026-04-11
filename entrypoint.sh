#!/usr/bin/env bash
set -euo pipefail

if [ -f /app/.env ]; then
  export $(grep -v '^\s*#' /app/.env | xargs -d '\n' 2>/dev/null || true)
fi

REQ="/app/source/requirements.txt"
SETUP="/app/setup.py"
MAIN="/app/source/main.py"

if [ "${SKIP_PIP_INSTALL:-0}" != "1" ]; then
  if [ -f "$REQ" ]; then
    echo "Installing requirements from $REQ"
    python -m pip install --upgrade pip
    python -m pip install --no-cache-dir -r "$REQ"
  else
    echo "No requirements found at $REQ — skipping install"
  fi
else
  echo "SKIP_PIP_INSTALL=1 — skipping pip install"
fi

if [ -f "$SETUP" ]; then
  echo "Running setup.py"
  python "$SETUP"
else
  echo "No setup.py — skipping"
fi

if [ -f "$MAIN" ]; then
  echo "Starting main: python -u $MAIN"
  exec python -u "$MAIN"
else
  echo "No main.py found at $MAIN — dropping to shell"
  exec /bin/bash
fi
