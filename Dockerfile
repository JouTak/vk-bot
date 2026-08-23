FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential gcc ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN useradd --create-home --shell /bin/bash bot \
    && mkdir -p /app/data \
    && chown -R bot:bot /app

WORKDIR /app

COPY vkbot/requirements.txt /app/vkbot/requirements.txt
RUN python -m pip install --upgrade pip \
    && python -m pip install --no-cache-dir -r /app/vkbot/requirements.txt

COPY vkbot /app/vkbot
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

USER bot

ENTRYPOINT ["/app/entrypoint.sh"]