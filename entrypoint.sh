#!/usr/bin/env bash
set -euo pipefail

if [ -f /app/.env ]; then
    export $(grep -v '^\s*#' /app/.env | xargs -d '
' 2>/dev/null || true)
fi

REQ="/app/vkbot/requirements.txt"

if [ "${SKIP_PIP_INSTALL:-0}" != "1" ]; then
    if [ -f "$REQ" ]; then
        echo "Installing requirements from $REQ"
        python -m pip install --upgrade pip || true
        python -m pip install --no-cache-dir -r "$REQ" \
            || echo "pip install failed — using build-time dependencies"
    fi
else
    echo "SKIP_PIP_INSTALL=1 — skipping pip install"
fi

cd /app
echo "Starting bot: python -u -m vkbot.bot.app"
exec python -u -m vkbot.bot.app