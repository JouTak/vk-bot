FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential gcc ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN useradd --create-home --shell /bin/bash bot \
    && mkdir -p /app \
    && chown bot:bot /app

WORKDIR /app

# Переходный период: зависимости обоих ботов
COPY source/requirements.txt /app/source/requirements.txt
COPY vkbot/requirements.txt /app/vkbot/requirements.txt
RUN python -m pip install --upgrade pip \
    && python -m pip install --no-cache-dir -r /app/source/requirements.txt \
    && python -m pip install --no-cache-dir -r /app/vkbot/requirements.txt

# Код: legacy (пока серверный entrypoint указывает на него) + новый
COPY source /app/source
COPY vkbot /app/vkbot

# entrypoint.sh не лежит в git (gitignore) — берётся из build context на сервере
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

USER bot

# Важно для СТАРОГО бота: у него относительные пути ./subscribers
WORKDIR /app/source

ENTRYPOINT ["/app/entrypoint.sh"]