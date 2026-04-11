from __future__ import annotations

from .db.db import session_scope
from .db.repositories import IgnoredRepository


class IgnoredList:
    def __init__(self):
        self.ignored = set()

    def add(self, uid):
        with session_scope() as s:
            repo = IgnoredRepository(s)
            if repo.add(int(uid)):
                self.ignored.add(int(uid))
                return f"Пользователь {uid} добавлен в игнор."
            return f"Пользователь {uid} уже в игноре."

    def remove(self, uid):
        with session_scope() as s:
            repo = IgnoredRepository(s)
            if repo.remove(int(uid)):
                self.ignored.discard(int(uid))
                return f"Пользователь {uid} удалён из игнора."
            return f"Пользователь {uid} не найден в списке игнорируемых."

    def is_ignored(self, uid):
        with session_scope() as s:
            repo = IgnoredRepository(s)
            return repo.is_ignored(int(uid))

    def clear(self):
        with session_scope() as s:
            repo = IgnoredRepository(s)
            repo.clear()
        self.ignored.clear()
        return "Список игнорируемых пользователей очищен."

    def save_to_file(self):
        # compatibility no-op
        return "Список игнорируемых сохранён."

    def load_from_file(self):
        with session_scope() as s:
            repo = IgnoredRepository(s)
            self.ignored = repo.list_all()
        return "Список игнорируемых загружен."
