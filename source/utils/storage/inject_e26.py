# -*- coding: utf-8 -*-
from __future__ import annotations
from pathlib import Path
from typing import Any
import urllib.request
import urllib.error
from ..db.db import is_database_enabled, session_scope
from ..db.repositories import UserRepository, UserDTO
from ..db.models import UserE26Model

E26_TSV_PATH = "./subscribers/ege26.txt"
E26_GSHEET_URL = "https://docs.google.com/spreadsheets/d/11aRURg_RU-WwaMs19xh5yE-_epG8Ea5fW-N8HGKBFZc/export?format=tsv&gid=1008955115"


def _parse_int(value: str, default: int = 0) -> int:
    if not value: return default
    try:
        return int(value.strip())
    except ValueError:
        return default


def _fetch_tsv_data() -> tuple[list[str], str]:
    try:
        req = urllib.request.Request(E26_GSHEET_URL, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            content = resp.read().decode("utf-8")
            lines = content.splitlines()
            if lines: return lines, "gsheet"
    except (urllib.error.URLError, TimeoutError):
        pass

    tsv_path = Path(E26_TSV_PATH)
    if tsv_path.exists():
        return tsv_path.read_text(encoding="utf-8").splitlines(), "file"
    return [], "none"


def _find_col(header_map: dict[str, int], *aliases: str) -> int | None:
    """Ищет колонку сначала по точному совпадению, затем по вхождению подстроки."""
    for alias in aliases:
        if alias in header_map:
            return header_map[alias]
    for alias in aliases:
        for key, idx in header_map.items():
            if alias in key:
                return idx
    return None


def inject_e26(vk_helper=None) -> dict[str, Any]:
    stats: dict[str, Any] = {"skipped": 0, "upserted": 0, "errors": [], "source": "none"}
    if not is_database_enabled(): return stats

    lines, source = _fetch_tsv_data()
    stats["source"] = source
    if not lines:
        if source == "none": stats["errors"].append("E26 inject skipped: no data source available")
        return stats

    header = [col.lower().strip() for col in lines[0].strip().split("\t")]
    header_map = {col: idx for idx, col in enumerate(header)}

    # Умный поиск колонок (поддерживает русские заголовки из таблицы)
    col_isu = _find_col(header_map, "ису", "айди", "id", "регистрации")
    col_uid = _find_col(header_map, "uid", "вк", "vk")
    col_fio = _find_col(header_map, "fio", "фио")
    col_nck = _find_col(header_map, "nck", "ник", "nick")
    col_qs1 = _find_col(header_map, "qs1", "вопрос 1", "вопрос1")
    col_scr = _find_col(header_map, "scr", "итого", "баллы", "score")
    col_plc = _find_col(header_map, "plc", "призовое место", "место", "place")

    if col_isu is None or col_uid is None:
        stats["errors"].append(f"Missing required columns: isu/айди and uid/вк. Found: {list(header_map.keys())}")
        return stats

    # Сбор VK-ссылок для ресолва
    vk_links_to_resolve: list[str] = []
    for line_idx, line in enumerate(lines[1:], start=1):
        parts = line.strip().split("\t")
        if col_uid is None or len(parts) <= col_uid: continue
        uid_raw = parts[col_uid].strip()
        if uid_raw and not uid_raw.lstrip("-").isdigit():
            vk_links_to_resolve.append(uid_raw)

    vk_link_to_uid: dict[str, int] = {}
    if vk_links_to_resolve and vk_helper:
        try:
            resolved_uids = vk_helper.links_to_uids(vk_links_to_resolve)
            for link, uid in zip(vk_links_to_resolve, resolved_uids):
                vk_link_to_uid[link] = uid if uid and uid > 1 else 1
        except Exception as e:
            stats["errors"].append(f"VK link resolution failed: {e}")
            for link in vk_links_to_resolve: vk_link_to_uid[link] = 1
    elif vk_links_to_resolve:
        for link in vk_links_to_resolve: vk_link_to_uid[link] = 1

    processed_isus: set[int] = set()
    for line_no, line in enumerate(lines[1:], start=2):
        parts = line.strip().split("\t")
        if not parts or all(not p.strip() for p in parts): continue

        def get_col(idx: int | None, default: str = "") -> str:
            return parts[idx].strip() if idx is not None and idx < len(parts) else default

        isu_raw = get_col(col_isu)
        is_external = isu_raw.lower() in ("внешний", "external", "ext")
        if not is_external:
            if not isu_raw or not isu_raw.isdigit():
                stats["errors"].append(f"Line {line_no}: invalid ISU '{isu_raw}'")
                stats["skipped"] += 1
                continue
            isu = int(isu_raw)
        else:
            isu = None

        uid_raw = get_col(col_uid)
        uid = 0
        if uid_raw:
            if uid_raw.lstrip("-").isdigit():
                uid = int(uid_raw)
            elif uid_raw in vk_link_to_uid:
                uid = vk_link_to_uid[uid_raw]
            else:
                uid = 1

        e26_data = {
            "uid": uid,
            "fio": get_col(col_fio),
            "nck": get_col(col_nck),
            "qs1": _parse_int(get_col(col_qs1)),
            "scr": _parse_int(get_col(col_scr)),
            "plc": _parse_int(get_col(col_plc)),
        }

        try:
            with session_scope() as s:
                repo = UserRepository(s)
                if is_external:
                    existing_by_uid = repo.get_by_uid(uid) if uid > 1 else None
                    if existing_by_uid:
                        isu = existing_by_uid.isu
                        new_met = dict(existing_by_uid.met);
                        new_met["e26"] = e26_data
                        dto = UserDTO(isu=isu, uid=uid, fio=existing_by_uid.fio or e26_data["fio"],
                                      grp=existing_by_uid.grp, nck=existing_by_uid.nck or e26_data["nck"], met=new_met)
                        repo.upsert(dto)
                    else:
                        dto = repo.add_with_auto_isu(uid=uid if uid > 1 else 0, fio=e26_data["fio"],
                                                     grp="", nck=e26_data["nck"], met={"e26": e26_data})
                        isu = dto.isu
                else:
                    existing = repo.get(isu)
                    if existing:
                        new_met = dict(existing.met);
                        new_met["e26"] = e26_data
                        new_uid = existing.uid
                        if uid > 1 and existing.uid in (0, 1): new_uid = uid
                        dto = UserDTO(isu=isu, uid=new_uid, fio=existing.fio, grp=existing.grp, nck=existing.nck,
                                      met=new_met)
                        repo.upsert(dto)
                    else:
                        dto = UserDTO(isu=isu, uid=uid if uid > 1 else 0, fio=e26_data["fio"],
                                      grp="", nck=e26_data["nck"], met={"e26": e26_data})
                        repo.upsert(dto)
                stats["upserted"] += 1
                processed_isus.add(isu)
        except Exception as e:
            stats["errors"].append(f"Line {line_no}: DB error - {e}")
            stats["skipped"] += 1

    # Очистка тех, кого больше нет в таблице
    try:
        with session_scope() as s:
            from sqlalchemy import select
            for row in s.execute(select(UserE26Model)).scalars().all():
                if row.isu not in processed_isus:
                    s.delete(row)
                    user = UserRepository(s).get(row.isu)
                    if user and "e26" in user.met:
                        new_met = dict(user.met);
                        del new_met["e26"]
                        UserRepository(s).upsert(
                            UserDTO(isu=user.isu, uid=user.uid, fio=user.fio, grp=user.grp, nck=user.nck, met=new_met))
    except Exception:
        pass
    return stats
