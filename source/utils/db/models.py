from __future__ import annotations

from typing import Any

from sqlalchemy import BigInteger, Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    pass


class UserModel(Base):
    __tablename__ = "users"

    isu: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=False)
    uid: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    fio: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    grp: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    nck: Mapped[str] = mapped_column(String(64), nullable=False, default="")



class UserA24Model(Base):
    __tablename__ = "user_a24"

    isu: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.isu", ondelete="CASCADE"),
        primary_key=True,
        autoincrement=False,
    )
    tsp: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    nck: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    lr1: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    wr1: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    wr2: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    nyt: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    fnl: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class UserS25Model(Base):
    __tablename__ = "user_s25"

    isu: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.isu", ondelete="CASCADE"),
        primary_key=True,
        autoincrement=False,
    )
    tsp: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    nck: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    wr1: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    rr1: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    wr2: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    rr2: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    fnl: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class UserY25Model(Base):
    __tablename__ = "user_y25"

    isu: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.isu", ondelete="CASCADE"),
        primary_key=True,
        autoincrement=False,
    )
    tsp: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    nck: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    nmb: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    bed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    way: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    car: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    liv: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    ugo: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class UserA25Model(Base):
    __tablename__ = "user_a25"

    isu: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.isu", ondelete="CASCADE"),
        primary_key=True,
        autoincrement=False,
    )
    fio: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    sts: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    uid: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    nck: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    cmd: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    cid: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    wr1: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    wr2: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    wr3: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    brs: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class IgnoredUserModel(Base):
    __tablename__ = "ignored_users"

    uid: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=False)


class UsersRawLineModel(Base):
    """
    Stores raw lines from legacy users.txt for full-fidelity migration / auditing.

    We store every parsed line here, even if it cannot be migrated into normalized tables.
    """
    __tablename__ = "users_raw_lines"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # 1-based line number in users.txt
    line_no: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    raw_line: Mapped[str] = mapped_column(Text, nullable=False)
    # optional parsed parts (best-effort)
    isu: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    uid: Mapped[int | None] = mapped_column(BigInteger, nullable=True, index=True)
    fio: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    grp: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    nck: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    met_json: Mapped[str] = mapped_column(Text, nullable=False, default="")
    # migration result
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="raw")  # ok | skipped | error | raw
    error: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        server_default=func.now(),
    )


class KVStoreModel(Base):
    """
    Small key/value store for operational state (optional but handy for future).
    Not used by current logic directly.
    """
    __tablename__ = "kv_store"

    k: Mapped[str] = mapped_column(String(128), primary_key=True)
    v: Mapped[str] = mapped_column(Text, nullable=False, default="")