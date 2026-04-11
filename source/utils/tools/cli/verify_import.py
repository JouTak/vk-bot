from __future__ import annotations

import json

import sqlalchemy as sa

from source.utils.db.db import init_engine, session_scope
from source.utils.db.models import UserModel, UsersRawLineModel


def _classify_file_lines(file_nonempty: list[str]) -> tuple[set[int], set[str]]:
    """
    Classify users.txt lines using the same rules as import_users_txt_to_db().

    New semantics:
      - If ISU is valid int, AND UID is parseable int (including 0/1),
        the line MUST exist in normalized `users` table.
      - If the line has any "soft issue" (uid 0/1, grp/nck format, etc),
        it MUST also exist in users_raw_lines (fix panel).
      - If ISU is not parseable -> cannot be in `users` and MUST be in raw.
      - If UID is not parseable -> cannot be in `users` (users.uid NOT NULL) and MUST be in raw.
    """
    should_normalize_isus: set[int] = set()
    should_be_raw_lines: set[str] = set()

    for ln in file_nonempty:
        parts = ln.split("\t")

        if len(parts) != 6:
            should_be_raw_lines.add(ln)
            continue

        isu = int(parts[0]) if parts[0].isdigit() else None
        uid = int(parts[1]) if parts[1].lstrip("-").isdigit() else None

        if isu is None or uid is None:
            should_be_raw_lines.add(ln)
            continue

        # must be in users
        should_normalize_isus.add(int(isu))

        # soft issues -> must be in raw too
        soft = False
        if 0 <= int(uid) <= 1:
            soft = True

        grp = (parts[3] or "").strip()
        if grp:
            if len(grp) != 5 or not ("A" <= grp[0] <= "Z") or not grp[1:].isdigit():
                soft = True

        nck = (parts[4] or "").strip()
        if nck:
            if " " in nck:
                soft = True
            else:
                for ch in nck:
                    if not (("a" <= ch.lower() <= "z") or ("0" <= ch <= "9") or ch == "_"):
                        soft = True
                        break
        if len(nck) > 64:
            soft = True

        # met_json validity affects raw presence (invalid JSON -> raw)
        try:
            parsed = json.loads(parts[5]) if parts[5] else {}
            if parsed is not None and not isinstance(parsed, dict):
                soft = True
        except Exception:
            soft = True

        if soft:
            should_be_raw_lines.add(ln)

    return should_normalize_isus, should_be_raw_lines


def main() -> None:
    """
    Verifies migration correctness with a clear summary.

    Rules:
    - Valid lines from users.txt MUST exist in normalized DB (users table, keyed by isu).
    - Invalid lines MUST be present in users_raw_lines.raw_line (full-fidelity backup).
    """
    init_engine()

    # If DB was reset and tables are missing, show a clear message instead of a huge traceback.
    try:
        import sqlalchemy as _sa
        from source.utils.db.models import UserModel as _UserModel

        with session_scope() as _s:
            _s.execute(_sa.select(_sa.func.count()).select_from(_UserModel)).scalar_one()
    except Exception:
        print("")
        print("VERIFY IMPORT (users.txt -> MySQL)")
        print("================================")
        print("Error: DB tables are missing.")
        print("Run: 1) Import users.txt -> DB")
        print("")
        raise SystemExit(1)

    users_txt_path = "source/subscribers/users.txt"

    file_nonempty: list[str] = []
    with open(users_txt_path, "r", encoding="utf-8") as f:
        for ln in f:
            ln = ln.rstrip("\n")
            if ln.strip():
                file_nonempty.append(ln)

    should_normalize_isus, should_be_raw_lines = _classify_file_lines(file_nonempty)

    with session_scope() as s:
        db_isus = set(int(x) for x in s.execute(sa.select(UserModel.isu)).scalars().all())
        # Raw table may contain both "error" lines and optionally a full copy of users.txt lines (depends on migration mode).
        db_raw_lines = set(str(x) for x in s.execute(sa.select(UsersRawLineModel.raw_line)).scalars().all())

    missing_in_users = sorted(should_normalize_isus - db_isus)
    extra_in_users = sorted(db_isus - should_normalize_isus)

    # Required raw lines are ONLY those that failed normalization.
    missing_required_raw = sorted(should_be_raw_lines - db_raw_lines)

    print("")
    print("VERIFY IMPORT (users.txt -> MySQL)")
    print("================================")
    print(f"file_nonempty_lines: {len(file_nonempty)}")
    print(f"should_normalize:    {len(should_normalize_isus)}")
    print(f"should_raw_required: {len(should_be_raw_lines)}")
    print(f"db_users:            {len(db_isus)}")
    print(f"db_raw_lines_total:  {len(db_raw_lines)}")
    print("")

    def _print_isu_list(title: str, items: list[int], limit: int = 100) -> None:
        print(f"{title}: {len(items)}")
        if not items:
            return
        print(f"{title} (first {min(limit, len(items))}):")
        for isu in items[:limit]:
            print(f"  {isu}")
        if len(items) > limit:
            print(f"  ... ({len(items) - limit} more)")

    def _print_raw_lines(title: str, items: list[str], limit: int = 20) -> None:
        print(f"{title}: {len(items)}")
        if not items:
            return
        print(f"{title} (first {min(limit, len(items))}):")
        for ln in items[:limit]:
            print("  ---")
            for line_part in str(ln).splitlines() or [""]:
                print(f"  {line_part}")
        if len(items) > limit:
            print(f"  ... ({len(items) - limit} more)")

    def _print_raw_ids_hint() -> None:
        print("")
        print("Hint:")
        print("  raw table contains invalid lines AND 'soft issue' lines used by Fix panel.")
        print("  extra_raw_lines > 0 usually means raw_lines are out of sync with users.txt classification.")
        print("  Recommended fix: re-run migration or inspect via raw_fixes list/show.")

    # Print ONLY deviations from 100% valid state (otherwise output stays short).
    print("")
    if not missing_in_users and not extra_in_users and not missing_required_raw:
        print("normalized_tables:   OK (all valid lines are in users; no unexpected users rows)")
    else:
        _print_isu_list("missing_in_users", missing_in_users)
        _print_isu_list("extra_in_users", extra_in_users)
        _print_raw_lines("missing_required_raw", missing_required_raw)

    # Raw table MUST contain all lines that require Fix panel (invalid + soft issues).
    extra_raw_lines = sorted(db_raw_lines - should_be_raw_lines)
    if not extra_raw_lines:
        print("raw_table:           OK (contains all required invalid/soft-issue lines)")
    else:
        print("raw_table:           WARN (contains extra lines not required by current classification)")
        print(f"extra_raw_lines:     {len(extra_raw_lines)}")
        _print_raw_ids_hint()

    print("")


if __name__ == "__main__":
    main()
