from __future__ import annotations

import json

import sqlalchemy as sa

from vkbot.domain.user import User
from vkbot.infrastructure.db.engine import init_engine, session_scope
from vkbot.infrastructure.db.models import UsersRawLineModel
from vkbot.infrastructure.db.repositories.user_repo import UserRepository

LEGACY_ALIASES = {"s24": "a24"}


def _validate(row) -> str | None:
    """Правила из старого cmd_apply. None = строка валидна."""
    if row.isu is None or row.uid is None:
        return "missing isu/uid"
    if 0 <= int(row.uid) <= 1:
        return "uid_invalid_0_1"
    nck = (row.nck or "").strip()
    if nck:
        if " " in nck or any(
                not (("a" <= ch.lower() <= "z") or ("0" <= ch <= "9") or ch == "_")
                for ch in nck
        ):
            return "nck_invalid_format"
        if len(nck) > 64:
            return "nck_too_long"
    grp = (row.grp or "").strip()
    if grp and (len(grp) != 5 or not ("A" <= grp[0] <= "Z") or not grp[1:].isdigit()):
        return "grp_invalid_format"
    try:
        met = json.loads(row.met_json) if row.met_json else {}
        if not isinstance(met, dict):
            raise ValueError
    except Exception:
        return "met_json_invalid"
    return None


def _list_problems(limit: int = 50) -> list:
    with session_scope() as s:
        rows = s.execute(
            sa.select(UsersRawLineModel)
            .where(UsersRawLineModel.status != "ok")
            .order_by(UsersRawLineModel.line_no, UsersRawLineModel.id)
            .limit(limit)
        ).scalars().all()
        return [
            (r.id, r.line_no, r.isu, r.uid, r.fio, r.grp, r.nck, r.error)
            for r in rows
        ]


def _prompt_keep(text: str, current) -> str:
    cur = "" if current is None else str(current)
    v = input(f"{text} [{cur}]: ").strip()
    return v if v else cur


def _edit(row_id: int) -> None:
    with session_scope() as s:
        row = s.get(UsersRawLineModel, row_id)
        if not row:
            print("not found")
            return

        print(f"\nline {row.line_no} | status={row.status} | error={row.error}")
        print(f"raw: {row.raw_line}")

        isu_raw = _prompt_keep("isu", row.isu)
        uid_raw = _prompt_keep("uid", row.uid)
        row.isu = int(isu_raw) if isu_raw.lstrip("-").isdigit() else None
        row.uid = int(uid_raw) if uid_raw.lstrip("-").isdigit() else None
        row.fio = _prompt_keep("fio", row.fio)
        row.grp = _prompt_keep("grp", row.grp)
        row.nck = _prompt_keep("nck", row.nck)

        # met_json: правим только если сломан
        if row.met_json:
            try:
                json.loads(row.met_json)
            except Exception:
                print("met_json invalid. Paste new JSON (finish with line 'END'):")
                lines = []
                while True:
                    ln = input()
                    if ln.strip() == "END":
                        break
                    lines.append(ln)
                row.met_json = "\n".join(lines).strip()

        # Apply: валидация + импорт в users
        err = _validate(row)
        if err:
            row.status = "error" if err in ("missing isu/uid", "met_json_invalid") else "skipped"
            row.error = err
            print(f"NOT applied: {err}")
            return

        met = json.loads(row.met_json) if row.met_json else {}
        met = {LEGACY_ALIASES.get(k, k): v for k, v in met.items()}
        user = User(
            isu=row.isu, uid=row.uid, fio=row.fio, grp=row.grp, nck=row.nck, met=met,
        )
        UserRepository(s).upsert(user)
        row.status = "ok"
        row.error = ""
        print("applied")


def main():
    init_engine()
    while True:
        items = _list_problems()
        if not items:
            print("No problem rows. All fixed!")
            return

        print("\nFix panel (status != ok):")
        for i, (rid, line_no, isu, uid, fio, grp, nck, err) in enumerate(items, start=1):
            print(f"  {i}) line={line_no} isu={isu} uid={uid} nck={nck} err={err}")
        print("  0) exit")

        sel = input("> ").strip()
        if sel == "0":
            return
        if sel.isdigit() and 1 <= int(sel) <= len(items):
            _edit(items[int(sel) - 1][0])


if __name__ == "__main__":
    main()
