from __future__ import annotations

import os
from pathlib import Path

from .db.db import is_database_enabled, session_scope
from .db.repositories import IgnoredRepository


class IgnoredList:
    def __init__(self):
        self.ignored: set[int] = set()
        self._db_enabled = is_database_enabled()

    def add(self, uid):
        uid = int(uid)
        if not self._db_enabled:
            if uid in self.ignored:
                return f"Пользователь {uid} уже в игноре."
            self.ignored.add(uid)
            self.save_to_file()
            return f"Пользователь {uid} добавлен в игнор."

        with session_scope() as s:
            repo = IgnoredRepository(s)
            if repo.add(uid):
                self.ignored.add(uid)
                return f"Пользователь {uid} добавлен в игнор."
            return f"Пользователь {uid} уже в игноре."

    def remove(self, uid):
        uid = int(uid)
        if not self._db_enabled:
            if uid in self.ignored:
                self.ignored.discard(uid)
                self.save_to_file()
                return f"Пользователь {uid} удалён из игнора."
            return f"Пользователь {uid} не найден в списке игнорируемых."

        with session_scope() as s:
            repo = IgnoredRepository(s)
            if repo.remove(uid):
                self.ignored.discard(uid)
                return f"Пользователь {uid} удалён из игнора."
            return f"Пользователь {uid} не найден в списке игнорируемых."

    def is_ignored(self, uid):
        uid = int(uid)
        if not self._db_enabled:
            return uid in self.ignored

        with session_scope() as s:
            repo = IgnoredRepository(s)
            return repo.is_ignored(uid)

    def clear(self):
        if not self._db_enabled:
            self.ignored.clear()
            self.save_to_file()
            return "Список игнорируемых пользователей очищен."

        with session_scope() as s:
            repo = IgnoredRepository(s)
            repo.clear()
        self.ignored.clear()
        return "Список игнорируемых пользователей очищен."

    def save_to_file(self):
        path = Path(os.getenv("IGNORED_TXT_PATH", "./subscribers/ignored.txt"))
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("w", encoding="utf-8") as f:
                f.write("\n".join(map(str, sorted(self.ignored))))
            return "Список игнорируемых сохранён."
        except Exception as e:
            return f"Ошибка при сохранении: {e}", True

    def load_from_file(self):
        path = Path(os.getenv("IGNORED_TXT_PATH", "./subscribers/ignored.txt"))
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            if not path.exists():
                path.write_text("", encoding="utf-8")

            raw = [ln.strip() for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()]
            ids: set[int] = set()
            for ln in raw:
                try:
                    ids.add(int(ln))
                except ValueError:
                    continue

            self.ignored = set(ids)

            if not self._db_enabled:
                return "Список игнорируемых загружен."

            with session_scope() as s:
                repo = IgnoredRepository(s)
                for uid in ids:
                    repo.add(uid)
                self.ignored = set(repo.list_all())

            return "Список игнорируемых загружен."
        except Exception as e:
            return f"Ошибка при загрузке: {e}", True
