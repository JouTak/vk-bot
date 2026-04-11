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


def load_db_config() -> DBConfig:
    """
    Loads DB config from environment (and optionally from local .env).

    Expected:
      - DATABASE_URL, e.g. mysql+pymysql://user:pass@127.0.0.1:3306/vk_bot?charset=utf8mb4
    """
    # Load env vars from local .env if present (does not override existing env)
    load_dotenv(override=False)

    url = os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError(
            "DATABASE_URL is not set. Example: "
            "mysql+pymysql://user:pass@127.0.0.1:3306/vk_bot?charset=utf8mb4"
        )
    return DBConfig(url=url)


_engine = None
_SessionLocal: sessionmaker | None = None


def init_engine(db_url: str | None = None) -> None:
    global _engine, _SessionLocal
    if _engine is not None and _SessionLocal is not None:
        return

    if db_url is None:
        db_url = load_db_config().url

    _engine = create_engine(
        db_url,
        pool_pre_ping=True,
        future=True,
    )
    _SessionLocal = sessionmaker(bind=_engine, autoflush=False, autocommit=False, future=True)


def get_engine():
    if _engine is None:
        init_engine()
    return _engine


@contextmanager
def session_scope() -> Session:
    if _SessionLocal is None:
        init_engine()
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
    """
    Session scope that FLUSHes (not commits) on successful exit.

    Useful when multiple operations must happen in one DB transaction controlled by a higher-level scope.
    """
    if _SessionLocal is None:
        init_engine()
    session: Session = _SessionLocal()  # type: ignore[misc]
    try:
        yield session
        session.flush()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
