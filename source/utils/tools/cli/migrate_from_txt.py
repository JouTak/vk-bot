from __future__ import annotations

import argparse
import os

from source.utils.db.db import get_engine, init_engine
from source.utils.db.models import Base
from source.utils.storage.user_store import import_users_txt_to_db


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db-url", dest="db_url", default=None)
    parser.add_argument("--users-txt", dest="users_txt", default=None)
    args = parser.parse_args()

    init_engine(args.db_url, force=True)
    engine = get_engine(force=True)
    Base.metadata.create_all(engine)

    users_txt = args.users_txt or os.path.join("source", "subscribers", "users.txt")
    users_txt = os.path.normpath(users_txt)

    imported = import_users_txt_to_db(users_txt)

    try:
        import sqlalchemy as sa
        from source.utils.db.db import session_scope
        from source.utils.db.models import UserModel

        with open(users_txt, "r", encoding="utf-8") as f:
            file_valid = 0
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

        print(f"Imported: {imported}")
        print(f"File valid rows (legacy semantics): {file_valid}")
        print(f"DB rows in users: {db_rows}")
    except Exception:
        print(f"Imported: {imported}")


if __name__ == "__main__":
    main()
