from __future__ import annotations

import sqlalchemy as sa

from source.utils.db.db import init_engine, session_scope
from source.utils.db.models import UsersRawLineModel


def main() -> None:
    init_engine()
    with session_scope() as s:
        rows = (
            s.execute(
                sa.select(UsersRawLineModel.line_no, UsersRawLineModel.isu, UsersRawLineModel.uid, UsersRawLineModel.error)
                .where(UsersRawLineModel.status == "error")
                .order_by(UsersRawLineModel.line_no)
                .limit(50)
            )
            .all()
        )

    for line_no, isu, uid, err in rows:
        print(f"{line_no}\tisu={isu}\tuid={uid}\t{err}")


if __name__ == "__main__":
    main()