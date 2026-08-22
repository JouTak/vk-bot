from __future__ import annotations

import urllib.request
import urllib.error
from pathlib import Path

from loguru import logger


def fetch_tsv(url: str | None, fallback_path: str | None) -> tuple[list[str], str]:
    """
    Скачивает TSV из Google Sheets, fallback на локальный файл.
    Возвращает (список строк, источник: "gsheet" | "file" | "none").
    """
    # 1. Пробуем Google Sheets
    if url:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                content = resp.read().decode("utf-8")
                lines = content.splitlines()
                if lines:
                    logger.info(f"Fetched {len(lines)} lines from Google Sheets")
                    return lines, "gsheet"
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            logger.warning(f"Google Sheets fetch failed: {e}")

    # 2. Fallback на локальный файл
    if fallback_path:
        path = Path(fallback_path)
        if path.exists():
            content = path.read_text(encoding="utf-8")
            lines = content.splitlines()
            if lines:
                logger.info(f"Fetched {len(lines)} lines from file: {fallback_path}")
                return lines, "file"

    return [], "none"
