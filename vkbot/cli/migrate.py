from __future__ import annotations

import argparse
import json

from sqlalchemy.orm import Session

from vkbot.domain.user import User
from vkbot.infrastructure.db.engine import init_engine, session_scope
from vkbot.infrastructure.db.models import UsersRawLineModel
from vkbot.infrastructure.db.repositories.user_repo import UserRepository

LEGACY_ALIASES = {"s24": "a24"}


def _soft_issues(uid, grp, nck, met_ok: bool) -> list[str]:
    issues = []
    if uid is not None and 0 <= uid <= 1:
        issues.append("uid_invalid_0_1")
    grp = (grp or "").strip()
    if grp and (len(grp) != 5 or not ("A" <= grp[0] <= "Z") or not grp[1:].isdigit()):
        issues.append("grp_invalid_format")
    nck = (nck or "").strip()
    if nck:
        if " " in nck or any(
                not (("a" <= ch.lower() <= "z") or ("0" <= ch <= "9") or ch == "_")
                for ch in nck
        ):
            issues.append("nck_invalid_format")
        elif len(nck) > 64:
            issues.append("nck_too_long")
    if not met_ok:
        issues.append("met_json_invalid")
    return issues


def _save_raw(
        s: Session, line_no: int, raw: str,
        isu, uid, fio, grp, nck, met_json, status: str, error: str,
) -> None:
    row = (
        s.query(UsersRawLineModel)
        .filter_by(line_no=line_no, raw_line=raw)
        .order_by(UsersRawLineModel.id.desc())
        .first()
    )
    if row is None:
        row = UsersRawLineModel(line_no=line_no, raw_line=raw)
        s.add(row)
    row.isu = isu
    row.uid = uid
    row.fio = fio
    row.grp = grp
    row.nck = nck
    row.met_json = met_json
    row.status = status
    row.error = error


def run_migration(users_txt: str) -> dict:
    stats = {"imported": 0, "raw": 0, "errors": 0}

    with open(users_txt, "r", encoding="utf-8") as f:
        lines = [ln.rstrip("\n") for ln in f if ln.strip()]

    for line_no, raw in enumerate(lines, start=1):
        parts = raw.split("\t")
        isu = int(parts[0]) if parts[0].isdigit() else None
        uid = int(parts[1]) if len(parts) > 1 and parts[1].lstrip("-").isdigit() else None
        fio = parts[2] if len(parts) > 2 else ""
        grp = parts[3] if len(parts) > 3 else ""
        nck = parts[4] if len(parts) > 4 else ""
        met_raw = parts[5] if len(parts) > 5 else ""

        met_ok = True
        met: dict = {}
        try:
            met = json.loads(met_raw) if met_raw else {}
            if not isinstance(met, dict):
                raise ValueError("met is not dict")
        except Exception:
            met_ok = False

        met = {LEGACY_ALIASES.get(k, k): v for k, v in met.items()}

        hard_error = ""
        if len(parts) != 6:
            hard_error = f"bad_columns:{len(parts)}"
        elif isu is None:
            hard_error = "isu_not_int"
        elif uid is None:
            hard_error = "uid_not_int"

        with session_scope() as s:
            if hard_error:
                _save_raw(s, line_no, raw, isu, uid, fio, grp, nck, met_raw, "error", hard_error)
                stats["errors"] += 1
                continue

            user = User(isu=isu, uid=uid, fio=fio, grp=grp, nck=nck, met=met)
            UserRepository(s).upsert(user)
            stats["imported"] += 1

            soft = _soft_issues(uid, grp, nck, met_ok)
            if soft:
                _save_raw(s, line_no, raw, isu, uid, fio, grp, nck, met_raw, "skipped", soft[0])
                stats["raw"] += 1

    return stats


def main():
    p = argparse.ArgumentParser(description="Import legacy users.txt into DB")
    p.add_argument("--users-txt", default="subscribers/users.txt")
    args = p.parse_args()

    init_engine()
    stats = run_migration(args.users_txt)
    print(f"Imported: {stats['imported']}")
    print(f"Raw (soft issues): {stats['raw']}")
    print(f"Errors: {stats['errors']}")


if __name__ == "__main__":
    main()
