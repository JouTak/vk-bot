from __future__ import annotations
"""
Ignored list storage.

Current source of truth: DB (IgnoredRepository).
Legacy compatibility: optional ignored.txt file (used by some deployments/scripts).

We keep both:
- read legacy file -> sync into DB
- save writes legacy file from in-memory set
"""

import os
from pathlib import Path

from .db.db import session_scope
from .db.repositories import IgnoredRepository


class IgnoredList:
    def __init__(self):
        self.ignored: set[int] = set()

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
        path = Path(os.getenv("IGNORED_TXT_PATH", "/app/data/subscribers/ignored.txt"))
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("w", encoding="utf-8") as f:
                f.write("\n".join(map(str, sorted(self.ignored))))
            return "Список игнорируемых сохранён."
        except Exception as e:
            return f"Ошибка при сохранении: {e}", True

    def load_from_file(self):
        path = Path(os.getenv("IGNORED_TXT_PATH", "/app/data/subscribers/ignored.txt"))
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

            # Update memory from legacy
            self.ignored = set(ids)

            # Sync DB (best effort), then prefer DB values
            with session_scope() as s:
                repo = IgnoredRepository(s)
                for uid in ids:
                    repo.add(uid)
                self.ignored = set(repo.list_all())

            return "Список игнорируемых загружен."
        except Exception as e:
            return f"Ошибка при загрузке: {e}", True