from __future__ import annotations

from datetime import datetime, timedelta

from vkbot.infrastructure.db.engine import session_scope
from vkbot.infrastructure.db.models import KVStoreModel


class WelcomeService:
    """Управление частотой приветственных сообщений (раз в 24 часа)."""

    def should_show_welcome(self, uid: int) -> bool:
        """Проверяет, прошло ли более 24 часов с последнего приветствия."""
        key = f"last_welcome:{uid}"
        with session_scope() as s:
            row = s.get(KVStoreModel, key)
            if not row:
                return True
            try:
                last = datetime.fromisoformat(row.v)
                return datetime.now() - last > timedelta(hours=24)
            except (ValueError, TypeError):
                return True

    def mark_welcome_shown(self, uid: int) -> None:
        """Сохраняет время показа приветствия пользователю."""
        key = f"last_welcome:{uid}"
        with session_scope() as s:
            row = s.get(KVStoreModel, key)
            if not row:
                row = KVStoreModel(k=key, v="")
                s.add(row)
            row.v = datetime.now().isoformat()
