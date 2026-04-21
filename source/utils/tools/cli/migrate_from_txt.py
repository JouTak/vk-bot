from __future__ import annotations

import argparse
import os
from pathlib import Path

import sqlalchemy as sa

try:
    from source.utils.db.db import get_engine, init_engine, session_scope
    from source.utils.db.models import Base, UserModel
    from source.utils.storage.user_store import import_users_txt_to_db
except ModuleNotFoundError:
    from utils.db.db import get_engine, init_engine, session_scope
    from utils.db.models import Base, UserModel
    from utils.storage.user_store import import_users_txt_to_db


def _resolve_users_txt(users_txt: str | None = None) -> str:
    if users_txt:
        return os.path.normpath(users_txt)

    here = Path(__file__).resolve()
    candidates = [
        Path("source") / "subscribers" / "users.txt",
        Path("subscribers") / "users.txt",
        here.parents[3] / "subscribers" / "users.txt",
        here.parents[4] / "source" / "subscribers" / "users.txt",
    ]

    for candidate in candidates:
        if candidate.exists():
            return os.path.normpath(str(candidate))

    return os.path.normpath(str(candidates[0]))


def run_migration(users_txt: str | None = None, db_url: str | None = None) -> dict[str, int | str]:
    init_engine(db_url, force=True)
    engine = get_engine(force=True)
    Base.metadata.create_all(engine)

    users_txt_path = _resolve_users_txt(users_txt)
    imported = import_users_txt_to_db(users_txt_path)

    file_valid = 0
    with open(users_txt_path, "r", encoding="utf-8") as f:
        for ln in f:
            ln = ln.strip()
            if not ln:
                continue
            parts = ln.split("\t")
            if len(parts) != 6 or not parts[0].isdigit():
                continue
            uid = int(parts[1]) if parts[1].lstrip("-").isdigit() else None
            if uid is None:
                continue
            file_valid += 1

    with session_scope() as s:
        db_rows = int(s.execute(sa.select(sa.func.count()).select_from(UserModel)).scalar_one())

    return {
        "users_txt": users_txt_path,
        "imported": imported,
        "file_valid_rows": file_valid,
        "db_rows_in_users": db_rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db-url", dest="db_url", default=None)
    parser.add_argument("--users-txt", dest="users_txt", default=None)
    args = parser.parse_args()

    report = run_migration(users_txt=args.users_txt, db_url=args.db_url)
    print(f'Users file: {report["users_txt"]}')
    print(f'Imported: {report["imported"]}')
    print(f'File valid rows (legacy semantics): {report["file_valid_rows"]}')
    print(f'DB rows in users: {report["db_rows_in_users"]}')


if __name__ == "__main__":
    main()
