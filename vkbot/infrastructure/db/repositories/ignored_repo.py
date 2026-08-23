from __future__ import annotations

from typing import cast
from sqlalchemy import delete
from sqlalchemy.orm import Session
from sqlalchemy.engine import CursorResult

from ..models import IgnoredUserModel


class IgnoredRepository:
    def __init__(self, session: Session):
        self.session = session

    def is_ignored(self, uid: int) -> bool:
        return self.session.get(IgnoredUserModel, uid) is not None

    def add(self, uid: int, reason: str = "") -> bool:
        if self.is_ignored(uid):
            return False
        self.session.add(IgnoredUserModel(uid=uid, reason=reason))
        return True

    def remove(self, uid: int) -> bool:
        result = cast(
            CursorResult,
            self.session.execute(
                delete(IgnoredUserModel).where(IgnoredUserModel.uid == uid)
            ),
        )
        return (result.rowcount or 0) > 0
