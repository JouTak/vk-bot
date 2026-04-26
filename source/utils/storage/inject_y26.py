# -*- coding: utf-8 -*-
"""
Y26 (Ягодное 2026) event data injection.

Reads TSV file subscribers/yagodnoe26.txt and upserts Y26 participant data
into the database using the generic UserEventModel (event_key='y26').
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from ..db.db import is_database_enabled, session_scope
from ..db.repositories import UserRepository, UserDTO
from ..db.models import UserEventModel


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
    
    TSV columns (expected header): isu, vkid, fio, nck, approve, number, bed, house, transport, money, cost
    
    Returns stats dict with counts.
    """
    stats = {"skipped": 0, "upserted": 0, "errors": [], "file_found": False}
    
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
    header = lines[0].strip().split("\t")
    header_map = {col.lower().strip(): idx for idx, col in enumerate(header)}
    
    # Required columns
    required = {"isu", "vkid"}
    if not required.issubset(header_map.keys()):
        stats["errors"].append(f"Missing required columns: {required - set(header_map.keys())}")
        return stats
    
    # Column indices
    col_isu = header_map.get("isu")
    col_vkid = header_map.get("vkid")
    col_fio = header_map.get("fio")
    col_nck = header_map.get("nck")
    col_approve = header_map.get("approve")
    col_number = header_map.get("number")
    col_bed = header_map.get("bed")
    col_house = header_map.get("house")
    col_transport = header_map.get("transport")
    col_money = header_map.get("money")
    col_cost = header_map.get("cost")
    
    # Collect VK links to resolve
    vk_links_to_resolve: list[str] = []
    for line in lines[1:]:
        parts = line.strip().split("\t")
        if len(parts) <= col_vkid:
            continue
        vkid_raw = parts[col_vkid].strip()
        if vkid_raw and not vkid_raw.lstrip("-").isdigit():
            vk_links_to_resolve.append(vkid_raw)
    
    # Resolve VK links to UIDs
    vk_link_to_uid: dict[str, int] = {}
    if vk_links_to_resolve and vk_helper:
        try:
            from ..vk_helper import links_to_uids
            vk_link_to_uid = links_to_uids(vk_helper, vk_links_to_resolve)
        except Exception as e:
            stats["errors"].append(f"VK link resolution failed: {e}")
    
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
        vkid_raw = get_col(col_vkid)
        uid = 0
        if vkid_raw:
            if vkid_raw.lstrip("-").isdigit():
                uid = int(vkid_raw)
            elif vkid_raw in vk_link_to_uid:
                uid = vk_link_to_uid[vkid_raw]
        
        # Build Y26 event data
        y26_data = {
            "fio": get_col(col_fio),
            "nck": get_col(col_nck),
            "nmb": get_col(col_number),
            "bed": _parse_bool(get_col(col_bed)),
            "house": get_col(col_house),
            "transport": get_col(col_transport),
            "money": _parse_bool(get_col(col_money)),
            "cost": _parse_int(get_col(col_cost)),
            "approve": _parse_bool(get_col(col_approve)),
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
                    if uid and uid != existing.uid:
                        # Update UID if different
                        dto = UserDTO(isu=isu, uid=uid, fio=existing.fio, grp=existing.grp, nck=existing.nck, met=new_met)
                    else:
                        dto = UserDTO(isu=isu, uid=existing.uid, fio=existing.fio, grp=existing.grp, nck=existing.nck, met=new_met)
                    repo.upsert(dto)
                else:
                    # Create new user with y26 data
                    dto = UserDTO(isu=isu, uid=uid, fio=y26_data.get("fio", ""), grp="", nck=y26_data.get("nck", ""), met={"y26": y26_data})
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
            from ..db.models import UserEventModel, UserModel
            
            # Find all y26 event records with matching house
            rows = s.execute(
                select(UserEventModel).where(UserEventModel.event_key == "y26")
            ).scalars().all()
            
            mates = []
            for row in rows:
                if row.isu == exclude_isu:
                    continue
                try:
                    data = json.loads(row.data_json) if row.data_json else {}
                except Exception:
                    continue
                
                row_house = (data.get("house") or "").strip().lower()
                if row_house == house.strip().lower():
                    nck = (data.get("nck") or "").strip()
                    if nck and nck != "-":
                        mates.append(nck)
            
            return ", ".join(sorted(mates)) if mates else ""
    except Exception:
        return ""
