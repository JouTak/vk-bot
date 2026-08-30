from __future__ import annotations

from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from loguru import logger

from vkbot.config import settings


class Base(DeclarativeBase):
    pass


_engine = None
_SessionLocal: sessionmaker | None = None


def init_engine() -> None:
    """Создаёт движок БД, сессии и синхронизирует схему."""
    global _engine, _SessionLocal

    _engine = create_engine(
        settings.database_url,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
        echo=False,
        future=True,
    )
    _SessionLocal = sessionmaker(bind=_engine, autoflush=False, future=True)

    # Создаём все таблицы, зарегистрированные в Base.metadata
    Base.metadata.create_all(_engine)

    try:
        from .schema_sync import sync_schema
        sync_schema(_engine)
    except Exception as e:
        logger.warning(f"schema_sync failed (non-fatal): {e}")


def get_engine():
    """Возвращает движок БД, при необходимости инициализирует его."""
    if _engine is None:
        init_engine()
    return _engine


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    """Контекстный менеджер сессии БД с коммитом и откатом."""
    if _SessionLocal is None:
        init_engine()
    session = _SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
