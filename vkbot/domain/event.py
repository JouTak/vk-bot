from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any


@dataclass
class EventDefinition:
    """Описание мероприятия."""
    key: str
    title: str
    active: bool = True
    fields: list[str] = field(default_factory=list)
    inject_url: str | None = None


@dataclass
class EventRegistration:
    """Данные юзера по конкретному событию."""
    isu: int
    event_key: str
    data: dict[str, Any] = field(default_factory=dict)

    def get(self, key: str, default: Any = None) -> Any:
        return self.data.get(key, default)

    def get_bool(self, key: str) -> bool:
        v = self.data.get(key)
        if isinstance(v, bool):
            return v
        if isinstance(v, str):
            return v.lower() in ("1", "true", "yes", "да")
        return bool(v)
