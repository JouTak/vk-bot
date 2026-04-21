from __future__ import annotations

import os
from contextlib import contextmanager
from dataclasses import dataclass

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker


@dataclass(frozen=True)
class DBConfig:
    url: str


def _load_env() -> None:
    load_dotenv(override=False)


def _is_truthy(value: str | None) -> bool:
    if value is None:
        return False
    return value.strip().lower() in {"1", "true", "yes", "y", "on", "db", "database", "sql", "mysql", "mariadb"}


def _is_falsy(value: str | None) -> bool:
    if value is None:
        return False
    return value.strip().lower() in {"0", "false", "no", "n", "off", "file", "files", "txt", "text"}


def get_storage_backend() -> str:
    _load_env()

    backend = os.getenv("STORAGE_BACKEND")
    if backend:
        normalized = backend.strip().lower()
        if normalized in {"db", "database", "sql", "mysql", "mariadb"}:
            return "db"
        if normalized in {"file", "files", "txt", "text"}:
            return "file"

    use_database = os.getenv("USE_DATABASE")
    if _is_truthy(use_database):
        return "db"
    if _is_falsy(use_database):
        return "file"

    return "file"


def is_database_enabled() -> bool:
    return get_storage_backend() == "db"


def load_db_config() -> DBConfig:
    _load_env()

    url = os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError(
            "DATABASE_URL is not set. Example: "
            "mysql+pymysql://user:pass@127.0.0.1:3306/vk_bot?charset=utf8mb4"
        )
    return DBConfig(url=url)


_engine = None
_SessionLocal: sessionmaker | None = None


def init_engine(db_url: str | None = None, force: bool = False) -> bool:
    global _engine, _SessionLocal

    if _engine is not None and _SessionLocal is not None:
        return True

    if not force and not is_database_enabled():
        return False

    if db_url is None:
        db_url = load_db_config().url

    _engine = create_engine(
        db_url,
        pool_pre_ping=True,
        future=True,
    )
    _SessionLocal = sessionmaker(bind=_engine, autoflush=False, autocommit=False, future=True)

    from .models import Base

    Base.metadata.create_all(_engine)
    return True


def get_engine(force: bool = False):
    if _engine is None:
        if not force and not is_database_enabled():
            raise RuntimeError("Database backend is disabled. Set STORAGE_BACKEND=db or USE_DATABASE=1.")
        init_engine(force=force)
    if _engine is None:
        raise RuntimeError("Database engine is not initialized.")
    return _engine


@contextmanager
def session_scope() -> Session:
    if _SessionLocal is None:
        if not is_database_enabled():
            raise RuntimeError("Database backend is disabled. Set STORAGE_BACKEND=db or USE_DATABASE=1.")
        init_engine()
    if _SessionLocal is None:
        raise RuntimeError("Database session factory is not initialized.")
    session: Session = _SessionLocal()  # type: ignore[misc]
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


@contextmanager
def session_scope_flush() -> Session:
    if _SessionLocal is None:
        if not is_database_enabled():
            raise RuntimeError("Database backend is disabled. Set STORAGE_BACKEND=db or USE_DATABASE=1.")
        init_engine()
    if _SessionLocal is None:
        raise RuntimeError("Database session factory is not initialized.")
    session: Session = _SessionLocal()  # type: ignore[misc]
    try:
        yield session
        session.flush()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
