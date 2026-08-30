from __future__ import annotations

import urllib.request
import urllib.error
from pathlib import Path

from loguru import logger


def fetch_tsv(url: str | None, fallback_path: str | None) -> tuple[list[str], str]:
    """
    Скачивает TSV из Google Sheets, fallback на локальный файл.

    При успешном скачивании из Google Sheets результат сохраняется в
    fallback_path как локальный кэш. При следующем запуске, если
    Google Sheets недоступен, будет использован этот кэш.

    Возвращает (список строк, источник: "gsheet" | "file" | "none").
    """
    lines: list[str] = []
    source: str = "none"

    # 1. Пробуем Google Sheets
    if url:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})

            with urllib.request.urlopen(req, timeout=15) as resp:
                content = resp.read().decode("utf-8")
                lines = content.splitlines()

                if lines:
                    logger.info(f"Fetched {len(lines)} lines from Google Sheets")
                    source = "gsheet"

        except Exception as e:
            logger.warning(f"Google Sheets fetch failed: {e}")

    # 2. При успехе — обновляем локальный кэш
    if source == "gsheet" and fallback_path:
        try:
            path = Path(fallback_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("\n".join(lines), encoding="utf-8")
            logger.debug(f"Cached {len(lines)} lines to {fallback_path}")
        except Exception as e:
            logger.warning(f"Failed to cache to {fallback_path}: {e}")

    # 3. Если из интернета ничего не пришло — читаем локальный кэш
    if source == "none" and fallback_path:
        try:
            path = Path(fallback_path)

            if path.exists():
                content = path.read_text(encoding="utf-8")
                lines = content.splitlines()

                if lines:
                    logger.info(f"Fetched {len(lines)} lines from file: {fallback_path}")
                    source = "file"

        except Exception as e:
            logger.warning(f"Local file fetch failed: {e}")

    return lines, source
