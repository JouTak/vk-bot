from __future__ import annotations

import sqlalchemy as sa

from source.utils.db.db import init_engine, session_scope
from source.utils.db.models import UserModel, UsersRawLineModel


def main() -> None:
    init_engine()
    with session_scope() as s:
        users = int(s.execute(sa.select(sa.func.count()).select_from(UserModel)).scalar_one())
        raw_total = int(s.execute(sa.select(sa.func.count()).select_from(UsersRawLineModel)).scalar_one())
        by_status = dict(
            s.execute(
                sa.select(UsersRawLineModel.status, sa.func.count())
                .group_by(UsersRawLineModel.status)
            ).all()
        )
        with_error = int(
            s.execute(
                sa.select(sa.func.count()).select_from(UsersRawLineModel).where(UsersRawLineModel.error != "")
            ).scalar_one()
        )

    print("users_rows", users)
    print("raw_lines_total", raw_total)
    print("raw_lines_by_status", by_status)
    print("raw_lines_with_error", with_error)


if __name__ == "__main__":
    main()