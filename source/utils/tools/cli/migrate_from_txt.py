from __future__ import annotations

import argparse
import os

from source.utils.db.db import get_engine, init_engine
from source.utils.db.models import Base
from source.utils.storage.user_store import import_users_txt_to_db


def run_migration(db_url: str | None = None, users_txt: str | None = None) -> dict[str, int | str]:
    init_engine(db_url, force=True)
    engine = get_engine(force=True)
    Base.metadata.create_all(engine)

    users_txt = users_txt or os.path.join("source", "subscribers", "users.txt")
    users_txt = os.path.normpath(users_txt)

    imported = import_users_txt_to_db(users_txt)

    file_valid = 0
    db_rows = 0

    try:
        import sqlalchemy as sa
        from source.utils.db.db import session_scope
        from source.utils.db.models import UserModel

        with open(users_txt, "r", encoding="utf-8") as f:
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
    except Exception:
        pass

    return {
        "imported": int(imported),
        "file_valid": int(file_valid),
        "db_rows": int(db_rows),
        "users_txt": users_txt,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db-url", dest="db_url", default=None)
    parser.add_argument("--users-txt", dest="users_txt", default=None)
    args = parser.parse_args()

    stats = run_migration(db_url=args.db_url, users_txt=args.users_txt)
    print(f"Imported: {stats['imported']}")
    print(f"File valid rows (legacy semantics): {stats['file_valid']}")
    print(f"DB rows in users: {stats['db_rows']}")
    print(f"Users txt: {stats['users_txt']}")


if __name__ == "__main__":
    main()
