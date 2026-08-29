from __future__ import annotations

from typing import cast
from sqlalchemy import delete
from sqlalchemy.orm import Session
from sqlalchemy.engine import CursorResult

from ..models import IgnoredUserModel


class IgnoredRepository:
    """Репозиторий пользователей, ожидающих админа."""

    def __init__(self, session: Session):
        """Сохраняет сессию БД."""
        self.session = session

    def is_ignored(self, uid: int) -> bool:
        """Проверяет, добавлен ли пользователь в список ожидания админа."""
        return self.session.get(IgnoredUserModel, uid) is not None

    def add(self, uid: int, reason: str = "") -> bool:
        """Добавляет пользователя в список ожидания админа."""
        if self.is_ignored(uid):
            return False
        self.session.add(IgnoredUserModel(uid=uid, reason=reason))
        return True

    def remove(self, uid: int) -> bool:
        """Удаляет пользователя из списка ожидания админа."""
        result = cast(
            CursorResult,
            self.session.execute(
                delete(IgnoredUserModel).where(IgnoredUserModel.uid == uid)
            ),
        )
        return (result.rowcount or 0) > 0
