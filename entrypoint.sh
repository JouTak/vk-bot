#!/usr/bin/env bash
set -euo pipefail

# --------------------------------------------------
# Load /app/.env without relying on xargs word splitting.
# Формат .env не меняется.
# --------------------------------------------------
if [ -f /app/.env ]; then
  while IFS= read -r line || [ -n "$line" ]; do
    # Убираем Windows-перевод строки
    line="${line%$'\r'}"

    # Убираем пробелы в начале строки
    line="${line#"${line%%[![:space:]]*}"}"

    # Пустые строки пропускаем
    [ -z "$line" ] && continue

    # Комментарии пропускаем
    case "$line" in
      \#*) continue ;;
    esac

    # Нужен формат KEY=VALUE
    if [[ "$line" != *"="* ]]; then
      continue
    fi

    key="${line%%=*}"
    val="${line#*=}"

    export "$key=$val"
  done < /app/.env
fi

REQ="/app/vkbot/requirements.txt"

# По умолчанию пропускаем pip install в рантайме.
# Зависимости уже должны быть установлены при сборке образа.
# Если нужно установить в рантайме: SKIP_PIP_INSTALL=0
if [ "${SKIP_PIP_INSTALL:-1}" != "1" ]; then
  if [ -f "$REQ" ]; then
    echo "Installing requirements from $REQ"
    python -m pip install --upgrade pip || true
    python -m pip install --no-cache-dir -r "$REQ" \
      || echo "pip install failed — using build-time dependencies"
  else
    echo "No requirements found at $REQ — skipping install"
  fi
else
  echo "SKIP_PIP_INSTALL=1 — skipping pip install"
fi

cd /app

echo "Starting bot: python -u -m vkbot.bot.app"
exec python -u -m vkbot.bot.app