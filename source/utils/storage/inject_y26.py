# -*- coding: utf-8 -*-
"""
Y26 (Ягодное 2026) event data injection.

Reads TSV file subscribers/yagodnoe26.txt and upserts Y26 participant data
into the database using the typed UserY26Model table.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from ..db.db import is_database_enabled, session_scope
from ..db.repositories import UserRepository, UserDTO
from ..db.models import UserY26Model


Y26_TSV_PATH = "./subscribers/yagodnoe26.txt"


def _parse_bool(value: str) -> bool:
    """Parse boolean from TSV cell."""
    if not value:
        return False
    v = value.strip().lower()
    return v in ("1", "true", "yes", "да", "y")


def _parse_int(value: str, default: int = 0) -> int:
    """Parse integer from TSV cell."""
    if not value:
        return default
    try:
        return int(value.strip())
    except ValueError:
        return default


def inject_y26(vk_helper=None) -> dict[str, Any]:
    """
    Read Y26 TSV file and inject participant data into DB.
    
    TSV columns: isu, uid, fio, nck, ugo, nmb, bed, hse, way, chk, cst
    
    Returns stats dict with counts.
    """
    stats: dict[str, Any] = {"skipped": 0, "upserted": 0, "errors": [], "file_found": False}
    
    if not is_database_enabled():
        return stats
    
    tsv_path = Path(Y26_TSV_PATH)
    if not tsv_path.exists():
        stats["errors"].append(f"Y26 inject skipped: file not found at {tsv_path}")
        return stats
    
    stats["file_found"] = True
    
    lines = tsv_path.read_text(encoding="utf-8").splitlines()
    if not lines:
        return stats
    
    # Parse header
    header = [col.lower().strip() for col in lines[0].strip().split("\t")]
    header_map = {col: idx for idx, col in enumerate(header)}
    
    # Required columns
    required = {"isu", "uid"}
    if not required.issubset(header_map.keys()):
        stats["errors"].append(f"Missing required columns: {required - set(header_map.keys())}")
        return stats
    
    # Column indices
    col_isu = header_map.get("isu")
    col_uid = header_map.get("uid")
    col_fio = header_map.get("fio")
    col_nck = header_map.get("nck")
    col_ugo = header_map.get("ugo")
    col_nmb = header_map.get("nmb")
    col_bed = header_map.get("bed")
    col_hse = header_map.get("hse")
    col_way = header_map.get("way")
    col_chk = header_map.get("chk")
    col_cst = header_map.get("cst")
    
    # Collect VK links to resolve
    vk_links_to_resolve: list[str] = []
    link_line_indices: list[int] = []
    for line_idx, line in enumerate(lines[1:], start=1):
        parts = line.strip().split("\t")
        if col_uid is None or len(parts) <= col_uid:
            continue
        uid_raw = parts[col_uid].strip()
        if uid_raw and not uid_raw.lstrip("-").isdigit():
            vk_links_to_resolve.append(uid_raw)
            link_line_indices.append(line_idx)
    
    # Resolve VK links to UIDs
    vk_link_to_uid: dict[str, int] = {}
    if vk_links_to_resolve and vk_helper:
        try:
            resolved_uids = vk_helper.links_to_uids(vk_links_to_resolve)
            for link, uid in zip(vk_links_to_resolve, resolved_uids):
                if uid and uid > 1:
                    vk_link_to_uid[link] = uid
                else:
                    # 1 = failed to resolve
                    vk_link_to_uid[link] = 1
        except Exception as e:
            stats["errors"].append(f"VK link resolution failed: {e}")
            # Mark all as unresolved
            for link in vk_links_to_resolve:
                vk_link_to_uid[link] = 1
    elif vk_links_to_resolve:
        # No vk_helper, mark as unresolved
        for link in vk_links_to_resolve:
            vk_link_to_uid[link] = 1
    
    # Process data rows
    for line_no, line in enumerate(lines[1:], start=2):
        parts = line.strip().split("\t")
        if not parts or all(not p.strip() for p in parts):
            continue
        
        def get_col(idx: int | None, default: str = "") -> str:
            if idx is None or idx >= len(parts):
                return default
            return parts[idx].strip()
        
        # Parse ISU
        isu_raw = get_col(col_isu)
        if not isu_raw or not isu_raw.isdigit():
            stats["errors"].append(f"Line {line_no}: invalid ISU '{isu_raw}'")
            stats["skipped"] += 1
            continue
        isu = int(isu_raw)
        
        # Parse VK ID
        uid_raw = get_col(col_uid)
        uid = 0
        if uid_raw:
            if uid_raw.lstrip("-").isdigit():
                uid = int(uid_raw)
            elif uid_raw in vk_link_to_uid:
                uid = vk_link_to_uid[uid_raw]
            else:
                uid = 1
        
        # Build Y26 event data
        y26_data = {
            "uid": uid,
            "fio": get_col(col_fio),
            "nck": get_col(col_nck),
            "nmb": get_col(col_nmb),
            "bed": _parse_bool(get_col(col_bed)),
            "hse": get_col(col_hse),
            "way": get_col(col_way),
            "chk": _parse_bool(get_col(col_chk)),
            "cst": _parse_int(get_col(col_cst)),
            "ugo": _parse_bool(get_col(col_ugo)),
        }
        
        # Upsert into DB
        try:
            with session_scope() as s:
                repo = UserRepository(s)
                existing = repo.get(isu)
                
                if existing:
                    # Update existing user, add y26 to met
                    new_met = dict(existing.met)
                    new_met["y26"] = y26_data
                    # Update main user uid if we have a valid one and existing doesn't
                    new_uid = existing.uid
                    if uid > 1 and existing.uid in (0, 1):
                        new_uid = uid
                    dto = UserDTO(isu=isu, uid=new_uid, fio=existing.fio, grp=existing.grp, nck=existing.nck, met=new_met)
                    repo.upsert(dto)
                else:
                    # Create new user with y26 data
                    dto = UserDTO(isu=isu, uid=uid if uid > 1 else 0, fio=y26_data.get("fio", ""), grp="", nck=y26_data.get("nck", ""), met={"y26": y26_data})
                    repo.upsert(dto)
                
                stats["upserted"] += 1
        except Exception as e:
            stats["errors"].append(f"Line {line_no}: DB error - {e}")
            stats["skipped"] += 1
    
    return stats


def get_y26_domik_mates(house: str, exclude_isu: int) -> str:
    """
    Get list of housemates for Y26 event.
    
    Returns comma-separated nicknames of people in the same house,
    excluding the user with exclude_isu.
    """
    if not house or house.lower() in ("-", "", "пока пусто"):
        return ""
    
    if not is_database_enabled():
        return ""
    
    try:
        from sqlalchemy import select
        with session_scope() as s:
            rows = s.execute(
                select(UserY26Model).where(UserY26Model.hse != "")
            ).scalars().all()
            
            mates = []
            for row in rows:
                if row.isu == exclude_isu:
                    continue
                
                row_house = (row.hse or "").strip().lower()
                if row_house == house.strip().lower():
                    nck = (row.nck or "").strip()
                    if nck and nck != "-":
                        mates.append(nck)
            
            return ", ".join(sorted(mates)) if mates else ""
    except Exception:
        return ""


if __name__ == "__main__":
    import sys
    import os
    
    # Change to source directory for relative paths
    script_dir = Path(__file__).parent
    source_dir = script_dir.parent.parent
    os.chdir(source_dir)
    
    # Initialize DB
    from utils.db.db import init_engine
    init_engine()
    
    # Try to get VK helper if possible
    vk_helper = None
    try:
        from utils import initialize
        import vk_api
        from vk_helper import VKHelper
        
        token, group_id = initialize()
        vk_session = vk_api.VkApi(token=token)
        vk_helper = VKHelper(vk_session, group_id)
        print("[Y26] VK helper initialized")
    except Exception as e:
        print(f"[Y26] Running without VK helper: {e}")
    
    # Run injection
    stats = inject_y26(vk_helper)
    
    if stats.get("file_found"):
        print(f"[Y26] Upserted: {stats.get('upserted', 0)}, skipped: {stats.get('skipped', 0)}")
    else:
        print("[Y26] File not found")
    
    if stats.get("errors"):
        for err in stats["errors"]:
            print(f"[Y26] Error: {err}")
