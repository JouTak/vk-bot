from __future__ import annotations

import argparse
import os

try:
    from source.utils.db.db import get_engine, init_engine, session_scope
    from source.utils.db.models import Base, UserA24Model, UserA25Model, UserEventModel, UserModel, UserS25Model, UserY25Model
    from source.utils.db.repositories import UserRepository
    from source.utils.storage.user_store import import_users_txt_to_db
except ModuleNotFoundError:
    from utils.db.db import get_engine, init_engine, session_scope
    from utils.db.models import Base, UserA24Model, UserA25Model, UserEventModel, UserModel, UserS25Model, UserY25Model
    from utils.db.repositories import UserRepository
    from utils.storage.user_store import import_users_txt_to_db


def _count_table(session, model) -> int:
    import sqlalchemy as sa

    return int(session.execute(sa.select(sa.func.count()).select_from(model)).scalar_one())


def run_migration(db_url: str | None = None, users_txt: str | None = None) -> dict[str, int | str]:
    init_engine(db_url, force=True)
    engine = get_engine(force=True)
    Base.metadata.create_all(engine)

    users_txt = users_txt or os.path.join("source", "subscribers", "users.txt")
    users_txt = os.path.normpath(users_txt)

    imported = import_users_txt_to_db(users_txt)
    legacy_alias_events = 0
    with session_scope() as s:
        legacy_alias_events = UserRepository(s).migrate_legacy_event_aliases()

    file_valid = 0
    stats = {
        "imported": int(imported),
        "legacy_alias_events": int(legacy_alias_events),
        "file_valid": 0,
        "db_rows": 0,
        "user_a24": 0,
        "user_s25": 0,
        "user_y25": 0,
        "user_a25": 0,
        "user_events": 0,
        "users_txt": users_txt,
    }

    try:
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
            stats["file_valid"] = int(file_valid)
            stats["db_rows"] = _count_table(s, UserModel)
            stats["user_a24"] = _count_table(s, UserA24Model)
            stats["user_s25"] = _count_table(s, UserS25Model)
            stats["user_y25"] = _count_table(s, UserY25Model)
            stats["user_a25"] = _count_table(s, UserA25Model)
            stats["user_events"] = _count_table(s, UserEventModel)
    except Exception:
        stats["file_valid"] = int(file_valid)

    return stats


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db-url", dest="db_url", default=None)
    parser.add_argument("--users-txt", dest="users_txt", default=None)
    args = parser.parse_args()

    stats = run_migration(db_url=args.db_url, users_txt=args.users_txt)
    print(f"Imported: {stats['imported']}")
    print(f"Legacy event aliases migrated: {stats['legacy_alias_events']}")
    print(f"File valid rows (legacy semantics): {stats['file_valid']}")
    print(f"DB rows in users: {stats['db_rows']}")
    print(f"Rows in user_a24: {stats['user_a24']}")
    print(f"Rows in user_s25: {stats['user_s25']}")
    print(f"Rows in user_y25: {stats['user_y25']}")
    print(f"Rows in user_a25: {stats['user_a25']}")
    print(f"Rows in user_events: {stats['user_events']}")
    print(f"Users txt: {stats['users_txt']}")


if __name__ == "__main__":
    main()
