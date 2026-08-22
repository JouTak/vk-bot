from __future__ import annotations

from typing import Any

from loguru import logger

from vkbot.infrastructure.db.event_registry import EventDef, get_event, get_active_events
from vkbot.infrastructure.sheets.fetcher import fetch_tsv
from vkbot.infrastructure.sheets.parsers import (
    parse_tsv_header,
    build_column_mapping,
    parse_row,
    find_column,
)
from .user_service import UserService


class EventService:
    """Генеричная инъекция данных ивентов из внешних источников."""

    def __init__(self, user_service: UserService, vk_client=None):
        self.user_service = user_service
        self.vk = vk_client

    def inject_event(self, event_key: str) -> dict[str, Any]:
        """
        Инъекция одного ивента. Возвращает статистику.
        """
        event_def = get_event(event_key)
        if event_def is None:
            return {"error": f"Unknown event: {event_key}", "upserted": 0, "skipped": 0}

        stats: dict[str, Any] = {"upserted": 0, "skipped": 0, "errors": [], "source": "none"}

        # 1. Скачать данные
        lines, source = fetch_tsv(event_def.inject_url, event_def.inject_file)
        stats["source"] = source

        if not lines:
            stats["errors"].append(f"No data source for {event_key}")
            return stats

        # 2. Парсим заголовок
        header_map = parse_tsv_header(lines[0])
        col_mapping = build_column_mapping(event_def, header_map)

        # Определяем колонки isu и uid (обязательные для инъекции)
        col_isu = find_column(header_map, "isu", "ису")
        col_uid = find_column(header_map, "uid", "вк", "vk", "vk_id", "vkid")

        if col_uid is None:
            stats["errors"].append(f"Missing uid column. Found: {list(header_map.keys())}")
            return stats

        # 3. Собираем VK-ссылки для резолвинга
        vk_links: list[str] = []
        for line in lines[1:]:
            parts = line.strip().split("\t")
            if col_uid is not None and col_uid < len(parts):
                uid_raw = parts[col_uid].strip()
                if uid_raw and not uid_raw.lstrip("-").isdigit():
                    vk_links.append(uid_raw)

        # Резолвим
        vk_link_to_uid: dict[str, int] = {}
        if vk_links and self.vk:
            try:
                resolved = self.vk.resolve_links(vk_links)
                for link, uid in zip(vk_links, resolved):
                    vk_link_to_uid[link] = uid if uid and uid > 1 else 1
            except Exception as e:
                stats["errors"].append(f"VK resolve failed: {e}")
                for link in vk_links:
                    vk_link_to_uid[link] = 1
        else:
            for link in vk_links:
                vk_link_to_uid[link] = 1

        # 4. Обрабатываем строки
        for line_no, line in enumerate(lines[1:], start=2):
            parts = line.strip().split("\t")
            if not parts or all(not p.strip() for p in parts):
                continue

            try:
                self._process_row(
                    parts=parts,
                    event_def=event_def,
                    col_mapping=col_mapping,
                    col_isu=col_isu,
                    col_uid=col_uid,
                    vk_link_to_uid=vk_link_to_uid,
                    stats=stats,
                )
            except Exception as e:
                stats["errors"].append(f"Line {line_no}: {e}")
                stats["skipped"] += 1

        logger.info(
            f"[{event_key}] Injection done: source={source}, "
            f"upserted={stats['upserted']}, skipped={stats['skipped']}, "
            f"errors={len(stats['errors'])}"
        )
        return stats

    def inject_all_active(self) -> dict[str, dict]:
        """Инъекция всех активных ивентов."""
        results = {}
        for event_def in get_active_events():
            if event_def.inject_url or event_def.inject_file:
                results[event_def.key] = self.inject_event(event_def.key)
        return results

    def _process_row(
            self,
            parts: list[str],
            event_def: EventDef,
            col_mapping: dict[str, int | None],
            col_isu: int | None,
            col_uid: int | None,
            vk_link_to_uid: dict[str, int],
            stats: dict,
    ) -> None:
        def get_col(idx: int | None, default: str = "") -> str:
            if idx is None or idx >= len(parts):
                return default
            return parts[idx].strip()

        # ISU
        isu_raw = get_col(col_isu)
        is_external = isu_raw.lower() in ("внешний", "внешний человек", "-", "external", "ext", "")
        isu: int | None = None
        if not is_external:
            if isu_raw.isdigit():
                isu = int(isu_raw)
            else:
                stats["skipped"] += 1
                return

        # UID
        uid_raw = get_col(col_uid)
        if not uid_raw or uid_raw == "-":
            stats["skipped"] += 1
            return

        if uid_raw.lstrip("-").isdigit():
            uid = int(uid_raw)
        elif uid_raw in vk_link_to_uid:
            uid = vk_link_to_uid[uid_raw]
        else:
            uid = 1

        if uid <= 1:
            stats["skipped"] += 1
            return

        # Парсим данные ивента по декларации
        event_data = parse_row(parts, event_def, col_mapping)

        # Upsert через UserService
        self.user_service.merge_injection_data(
            isu=isu,
            uid=uid,
            fio=event_data.get("fio", ""),
            grp="",
            nck=event_data.get("nck", ""),
            event_key=event_def.key,
            event_data=event_data,
        )
        stats["upserted"] += 1
