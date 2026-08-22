from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any


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
        return 100000 <= self.isu <= 999999

    @property
    def has_valid_uid(self) -> bool:
        return self.uid > 1

    @property
    def display_name(self) -> str:
        return self.fio or self.nck or f"id{self.uid}"

    def get_event_data(self, event_key: str) -> dict[str, Any]:
        return self.met.get(event_key, {})

    def has_event(self, event_key: str) -> bool:
        return event_key in self.met