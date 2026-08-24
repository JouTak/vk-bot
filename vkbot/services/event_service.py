from __future__ import annotations

from typing import Any

from loguru import logger

from vkbot.infrastructure.db.event_registry import EventDef, get_event, get_active_events
from vkbot.infrastructure.sheets.fetcher import fetch_tsv
from vkbot.infrastructure.sheets.parsers import (
    parse_tsv_header,
    parse_row,
    build_column_mapping_verbose,
    find_column_verbose,
)
from vkbot.infrastructure.db.engine import session_scope
from vkbot.infrastructure.db.repositories.user_repo import UserRepository
from .user_service import UserService


class EventService:
    """Генеричная инъекция данных ивентов из внешних источников."""

    def __init__(self, user_service: UserService | None = None, vk_client=None):
        self.user_service = user_service
        self.vk = vk_client

    def inject_event(self, event_key: str) -> dict[str, Any]:
        """
        Инъекция одного ивента.
        Сначала скачиваем и парсим вне БД-сессии, потом пишем в БД.
        """
        prepared, stats = self.prepare_event(event_key)

        if prepared:
            with session_scope() as s:
                user_svc = UserService(UserRepository(s))

                for item in prepared:
                    try:
                        user_svc.merge_injection_data(
                            isu=item["isu"],
                            uid=item["uid"],
                            fio=item["fio"],
                            grp=item["grp"],
                            nck=item["nck"],
                            event_key=event_key,
                            event_data=item["event_data"],
                        )
                        stats["upserted"] += 1
                    except Exception as e:
                        stats["errors"].append(f"Write row uid={item.get('uid')}: {e}")
                        stats["skipped"] += 1

        logger.info(
            f"[{event_key}] Injection done: source={stats.get('source')}, "
            f"upserted={stats.get('upserted')}, skipped={stats.get('skipped')}, "
            f"errors={len(stats.get('errors', []))}"
        )

        return stats

    def inject_all_active(self) -> dict[str, dict]:
        """Инъекция всех активных ивентов."""
        results = {}

        for event_def in get_active_events():
            if event_def.inject_url or event_def.inject_file:
                results[event_def.key] = self.inject_event(event_def.key)

        return results

    def prepare_event(self, event_key: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        """
        Скачивает и парсит ивент без записи в БД.
        Возвращает подготовленные строки и статистику.
        """
        event_def = get_event(event_key)
        stats: dict[str, Any] = {
            "upserted": 0,
            "skipped": 0,
            "errors": [],
            "source": "none",
        }

        if event_def is None:
            stats["errors"].append(f"Unknown event: {event_key}")
            return [], stats

        lines, source = fetch_tsv(event_def.inject_url, event_def.inject_file)
        stats["source"] = source

        if not lines:
            stats["errors"].append(f"No data source for {event_key}")
            return [], stats

        header_map = parse_tsv_header(lines[0])

        col_mapping, mapping_warnings = build_column_mapping_verbose(event_def, header_map)
        for warning in mapping_warnings:
            logger.warning(f"[{event_key}] {warning}")

        col_isu, isu_how = find_column_verbose(header_map, "isu", "ису")
        col_uid, uid_how = find_column_verbose(
            header_map,
            "uid",
            "вк",
            "vk",
            "vk_id",
            "vkid",
        )
        col_grp, grp_how = find_column_verbose(
            header_map,
            "grp",
            "group",
            "группа",
        )

        if col_isu is not None and isu_how != "exact":
            logger.warning(f"[{event_key}] ISU column matched as: {isu_how}")

        if col_uid is None:
            stats["errors"].append(
                f"Missing uid column ({uid_how}). Found: {list(header_map.keys())}"
            )
            return [], stats

        if uid_how != "exact":
            logger.warning(f"[{event_key}] UID column matched as: {uid_how}")

        if col_grp is not None and grp_how != "exact":
            logger.warning(f"[{event_key}] GRP column matched as: {grp_how}")

        vk_links: list[str] = []
        for line in lines[1:]:
            parts = line.strip().split("\t")
            if col_uid is not None and col_uid < len(parts):
                uid_raw = parts[col_uid].strip()
                if uid_raw and not uid_raw.lstrip("-").isdigit():
                    vk_links.append(uid_raw)

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
                vk_link_to_uid[link] = 1    # unresolved

        prepared: list[dict[str, Any]] = []

        for line_no, line in enumerate(lines[1:], start=2):
            parts = line.strip().split("\t")
            if not parts or all(not p.strip() for p in parts):
                continue
            try:
                item = self._prepare_row(
                    parts=parts,
                    event_def=event_def,
                    col_mapping=col_mapping,
                    col_isu=col_isu,
                    col_uid=col_uid,
                    col_grp=col_grp,
                    vk_link_to_uid=vk_link_to_uid,
                    stats=stats,
                )
                if item is not None:
                    prepared.append(item)
            except Exception as e:
                stats["errors"].append(f"Line {line_no}: {e}")
                stats["skipped"] += 1

        return prepared, stats

    @staticmethod
    def _prepare_row(
        parts: list[str],
        event_def: EventDef,
        col_mapping: dict[str, int | None],
        col_isu: int | None,
        col_uid: int | None,
        col_grp: int | None,
        vk_link_to_uid: dict[str, int],
        stats: dict,
    ) -> dict[str, Any] | None:
        def get_col(idx: int | None, default: str = "") -> str:
            if idx is None or idx >= len(parts):
                return default
            return parts[idx].strip()

        # ISU
        isu_raw = get_col(col_isu)
        is_external = isu_raw.lower() in (
            "внешний",
            "внешний человек",
            "-",
            "external",
            "ext",
            "",
        )

        isu: int | None = None

        if not is_external:
            if isu_raw.isdigit():
                isu = int(isu_raw)
            else:
                stats["skipped"] += 1
                return None

        # UID
        uid_raw = get_col(col_uid)

        if not uid_raw or uid_raw == "-":
            stats["skipped"] += 1
            return None

        if uid_raw.lstrip("-").isdigit():
            uid = int(uid_raw)
        elif uid_raw in vk_link_to_uid:
            uid = vk_link_to_uid[uid_raw]
        else:
            uid = 1

        if uid <= 1:
            stats["skipped"] += 1
            return None

        # Данные ивента
        event_data = parse_row(parts, event_def, col_mapping)

        # Группа из отдельной колонки, если она есть
        grp = get_col(col_grp)

        return {
            "isu": isu,
            "uid": uid,
            "fio": event_data.get("fio", ""),
            "grp": grp,
            "nck": event_data.get("nck", ""),
            "event_data": event_data,
        }