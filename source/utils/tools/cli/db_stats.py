from __future__ import annotations

import sqlalchemy as sa

from source.utils.db.db import init_engine, session_scope
from source.utils.db.models import (
    IgnoredUserModel,
    UserA24Model,
    UserA25Model,
    UserModel,
    UserS25Model,
    UserY25Model,
    UsersRawLineModel,
)


def main() -> None:
    """
    DB stats (compact):
    - users_total
    - raw_lines_total + raw_top_errors (top-10)
    """
    init_engine()

    with session_scope() as s:
        users_total = int(s.execute(sa.select(sa.func.count()).select_from(UserModel)).scalar_one())
        raw_total = int(s.execute(sa.select(sa.func.count()).select_from(UsersRawLineModel)).scalar_one())
        top_errors = s.execute(
            sa.select(UsersRawLineModel.error, sa.func.count())
            .where(UsersRawLineModel.error != "")
            .group_by(UsersRawLineModel.error)
            .order_by(sa.func.count().desc())
            .limit(10)
        ).all()

    print("Users:", users_total)
    print("Raw lines:", raw_total)
    if top_errors:
        print("Top raw errors:")
        for err, cnt in top_errors:
            print(f"  {cnt}  {err}")


if __name__ == "__main__":
    main()
