from __future__ import annotations

import sqlalchemy as sa

from vkbot.infrastructure.db.engine import init_engine, session_scope
from vkbot.infrastructure.db.event_registry import EVENT_REGISTRY
from vkbot.infrastructure.db.models import EVENT_MODELS, UserModel, UsersRawLineModel


def main():
    init_engine()
    with session_scope() as s:
        users_total = int(s.execute(
            sa.select(sa.func.count()).select_from(UserModel)
        ).scalar_one())
        raw_total = int(s.execute(
            sa.select(sa.func.count()).select_from(UsersRawLineModel)
        ).scalar_one())
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

        print("Events:")
        for key, model in EVENT_MODELS.items():
            cnt = int(s.execute(
                sa.select(sa.func.count()).select_from(model)
            ).scalar_one())
            print(f"  {key} ({EVENT_REGISTRY[key].title}): {cnt}")


if __name__ == "__main__":
    main()
