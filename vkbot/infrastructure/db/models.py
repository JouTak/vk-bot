from __future__ import annotations

from sqlalchemy import BigInteger, Boolean, Integer, String, Text, DateTime, ForeignKey, Column
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from .engine import Base
from .event_registry import EVENT_REGISTRY, EventDef, FieldDef


# ============================================================
# Базовые таблицы (пишутся вручную, они стабильны)
# ============================================================

class UserModel(Base):
    __tablename__ = "users"

    isu: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=False)
    uid: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    fio: Mapped[str] = mapped_column(String(255), default="")
    grp: Mapped[str] = mapped_column(String(64), default="")
    nck: Mapped[str] = mapped_column(String(64), default="")
    created_at: Mapped[str | None] = mapped_column(DateTime, server_default=func.now())
    last_seen_at: Mapped[str | None] = mapped_column(DateTime, nullable=True)


class IgnoredUserModel(Base):
    __tablename__ = "ignored_users"
    uid: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    reason: Mapped[str] = mapped_column(String(255), default="")


class KVStoreModel(Base):
    __tablename__ = "kv_store"
    k: Mapped[str] = mapped_column(String(128), primary_key=True)
    v: Mapped[str] = mapped_column(Text, default="")


class UsersRawLineModel(Base):
    __tablename__ = "users_raw_lines"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    line_no: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    raw_line: Mapped[str] = mapped_column(Text, nullable=False)
    isu: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    uid: Mapped[int | None] = mapped_column(BigInteger, nullable=True, index=True)
    fio: Mapped[str] = mapped_column(String(255), default="")
    grp: Mapped[str] = mapped_column(String(64), default="")
    nck: Mapped[str] = mapped_column(String(64), default="")
    met_json: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(32), default="raw")
    error: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[str | None] = mapped_column(DateTime, server_default=func.now())


# ============================================================
# Генерация таблиц ивентов из деклараций
# ============================================================

_TYPE_MAP = {
    "int": Integer,
    "str": String(255),
    "bool": Boolean,
}


def _build_event_table(event: EventDef) -> type:
    """
    Генерирует ORM-модель для ивента из его декларации.
    Вызывается один раз при импорте модуля.
    """
    # Базовые атрибуты таблицы
    attrs: dict = {
        "__tablename__": event.table_name,
        "isu": mapped_column(
            Integer,
            ForeignKey("users.isu", ondelete="CASCADE"),
            primary_key=True,
            autoincrement=False,
        ),
    }

    # Добавляем колонки из декларации
    for field_def in event.fields:
        default = field_def.default

        if field_def.type == "str":
            attrs[field_def.name] = mapped_column(String(255), default=default or "")
        elif field_def.type == "int":
            attrs[field_def.name] = mapped_column(Integer, default=default or 0)
        elif field_def.type == "bool":
            attrs[field_def.name] = mapped_column(Boolean, default=bool(default))

    # Создаём класс динамически
    cls_name = f"User{event.key.capitalize()}Model"
    model_cls = type(cls_name, (Base,), attrs)
    return model_cls


# Генерируем все модели и сохраняем ссылки
EVENT_MODELS: dict[str, type] = {}

for _event_def in EVENT_REGISTRY.values():
    _model = _build_event_table(_event_def)
    EVENT_MODELS[_event_def.key] = _model


def get_event_model(event_key: str):
    """Достать ORM-модель по ключу ивента."""
    return EVENT_MODELS.get(event_key)
