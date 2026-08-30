from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any
from vkbot.domain.rules import is_real_isu, is_valid_uid


@dataclass
class User:
    """Чистый доменный объект. Никакой логики БД или VK."""
    isu: int
    uid: int
    fio: str = ""
    grp: str = ""
    nck: str = ""
    met: dict[str, dict[str, Any]] = field(default_factory=dict)

    @property
    def has_real_isu(self) -> bool:
        """Возвращает True, если у пользователя настоящий ISU."""
        return is_real_isu(self.isu)

    @property
    def has_valid_uid(self) -> bool:
        """Возвращает True, если у пользователя валидный VK ID."""
        return is_valid_uid(self.uid)

    @property
    def display_name(self) -> str:
        """Возвращает отображаемое имя: ФИО, ник или id."""
        return self.fio or self.nck or f"id{self.uid}"

    def get_event_data(self, event_key: str) -> dict[str, Any]:
        """Возвращает данные пользователя по ключу ивента."""
        return self.met.get(event_key, {})

    def has_event(self, event_key: str) -> bool:
        """Проверяет наличие данных пользователя по ивенту."""
        return event_key in self.met