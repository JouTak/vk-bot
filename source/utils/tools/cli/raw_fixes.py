from __future__ import annotations

import argparse
import json

import sqlalchemy as sa

from source.utils.db.db import init_engine, session_scope
from source.utils.db.models import UsersRawLineModel
from source.utils.db.repositories import UserRepository, UserDTO


def cmd_list(limit: int) -> None:
    init_engine()
    with session_scope() as s:
        rows = (
            s.execute(
                sa.select(
                    UsersRawLineModel.id,
                    UsersRawLineModel.line_no,
                    UsersRawLineModel.isu,
                    UsersRawLineModel.uid,
                    UsersRawLineModel.error,
                )
                .where(UsersRawLineModel.status != "ok")
                .order_by(UsersRawLineModel.line_no, UsersRawLineModel.id)
                .limit(limit)
            )
            .all()
        )
    for rid, line_no, isu, uid, err in rows:
        print(f"{rid}\tline={line_no}\tisu={isu}\tuid={uid}\t{err}")


def cmd_show(raw_id: int) -> None:
    init_engine()
    with session_scope() as s:
        row = s.get(UsersRawLineModel, raw_id)
        if not row:
            raise SystemExit(f"raw row id={raw_id} not found")
        print("id", row.id)
        print("line_no", row.line_no)
        print("status", row.status)
        print("error", row.error)
        print("raw_line", row.raw_line)
        print("parsed isu", row.isu)
        print("parsed uid", row.uid)
        print("fio", row.fio)
        print("grp", row.grp)
        print("nck", row.nck)
        print("met_json", row.met_json)


def cmd_update(raw_id: int, isu: int | None, uid: int | None, fio: str | None, grp: str | None, nck: str | None, met_json: str | None) -> None:
    init_engine()
    with session_scope() as s:
        row = s.get(UsersRawLineModel, raw_id)
        if not row:
            raise SystemExit(f"raw row id={raw_id} not found")

        if isu is not None:
            row.isu = isu
        if uid is not None:
            row.uid = uid
        if fio is not None:
            row.fio = fio
        if grp is not None:
            row.grp = grp
        if nck is not None:
            row.nck = nck
        if met_json is not None:
            # validate json
            json.loads(met_json) if met_json else {}
            row.met_json = met_json

        row.status = "edited"
        row.error = ""
    print("updated")


def cmd_apply(raw_id: int) -> None:
    """Try to import one raw row into normalized tables.

    Notes about "soft issues":
      - Some fields can be "non-ideal" but still allowed for normalized import.
      - Those issues should still keep the row in fix panel until resolved.
        We model them as status="skipped" + specific error code.
    """
    init_engine()
    with session_scope() as s:
        row = s.get(UsersRawLineModel, raw_id)
        if not row:
            raise SystemExit(f"raw row id={raw_id} not found")

        if row.isu is None or row.uid is None:
            row.status = "error"
            row.error = "missing isu/uid"
            return

        # With the new semantics, rows are already stored in normalized tables (users),
        # and cmd_apply is used only to check if the raw row can be considered "fixed"
        # (so it can disappear from Fix panel).
        #
        # uid 0/1 is a "soft issue": do not mark ok until it is fixed.
        if 0 <= int(row.uid) <= 1:
            row.status = "skipped"
            row.error = "uid_invalid_0_1"
            return

        # "soft" issue: prefer nck without spaces and only [A-Za-z0-9_]
        nck = (row.nck or "").strip()
        if nck:
            if " " in nck:
                row.status = "skipped"
                row.error = "nck_invalid_format"
                return
            for ch in nck:
                if not (("a" <= ch.lower() <= "z") or ("0" <= ch <= "9") or ch == "_"):
                    row.status = "skipped"
                    row.error = "nck_invalid_format"
                    return
        if len(nck) > 64:
            row.status = "skipped"
            row.error = "nck_too_long"
            return

        # grp format is also a "soft issue" (imported into users, but should be fixed for cleanliness).
        grp = (row.grp or "").strip()
        if grp:
            if len(grp) != 5 or not ("A" <= grp[0] <= "Z") or not grp[1:].isdigit():
                row.status = "skipped"
                row.error = "grp_invalid_format"
                return

        # met_json must be valid JSON object to be considered ok in fix panel
        try:
            met = json.loads(row.met_json) if row.met_json else {}
            if met is not None and not isinstance(met, dict):
                raise ValueError("met_json_not_object")
        except Exception:
            row.status = "error"
            row.error = "met_json_invalid"
            return

        row.status = "ok"
        row.error = ""

    print("applied")


def cmd_apply_all() -> None:
    init_engine()
    with session_scope() as s:
        ids = (
            s.execute(
                sa.select(UsersRawLineModel.id)
                .where(UsersRawLineModel.status != "ok")
                .order_by(UsersRawLineModel.line_no, UsersRawLineModel.id)
            )
            .scalars()
            .all()
        )

    applied = 0
    for rid in ids:
        try:
            cmd_apply(int(rid))
            applied += 1
        except Exception:
            # keep going; errors are stored into row.error by cmd_apply where possible
            continue
    print("processed", applied)


def main() -> None:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)

    p_list = sub.add_parser("list")
    p_list.add_argument("--limit", type=int, default=50)

    p_show = sub.add_parser("show")
    p_show.add_argument("id", type=int)

    p_upd = sub.add_parser("update")
    p_upd.add_argument("id", type=int)
    p_upd.add_argument("--isu", type=int, default=None)
    p_upd.add_argument("--uid", type=int, default=None)
    p_upd.add_argument("--fio", type=str, default=None)
    p_upd.add_argument("--grp", type=str, default=None)
    p_upd.add_argument("--nck", type=str, default=None)
    p_upd.add_argument("--met-json", type=str, default=None)

    p_apply = sub.add_parser("apply")
    p_apply.add_argument("id", type=int)

    sub.add_parser("apply-all")

    args = p.parse_args()

    if args.cmd == "list":
        cmd_list(args.limit)
    elif args.cmd == "show":
        cmd_show(args.id)
    elif args.cmd == "update":
        cmd_update(args.id, args.isu, args.uid, args.fio, args.grp, args.nck, args.met_json)
    elif args.cmd == "apply":
        cmd_apply(args.id)
    elif args.cmd == "apply-all":
        cmd_apply_all()
    else:
        raise SystemExit("unknown cmd")


if __name__ == "__main__":
    main()
