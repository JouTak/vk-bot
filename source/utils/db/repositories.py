from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sqlalchemy import and_, delete, select
from sqlalchemy.orm import Session

from .models import (
    IgnoredUserModel,
    UserA24Model,
    UserA25Model,
    UserModel,
    UserS25Model,
    UserY25Model,
)


@dataclass
class UserDTO:
    isu: int
    uid: int
    fio: str
    grp: str
    nck: str
    met: dict[str, Any]


def _bool(v: Any) -> bool:
    return bool(v) if v is not None else False


class UserRepository:
    """
    Stores base user fields in users table and event-specific metadata in separate 1:1 tables.
    Public API keeps met as dict for backward compatibility with bot logic.
    """

    def __init__(self, session: Session):
        self.session = session

    def get(self, isu: int) -> UserDTO | None:
        u = self.session.get(UserModel, isu)
        if not u:
            return None

        met: dict[str, Any] = {}

        a24 = self.session.get(UserA24Model, isu)
        if a24:
            met["a24"] = {
                "tsp": int(a24.tsp),
                "nck": a24.nck,
                "lr1": _bool(a24.lr1),
                "wr1": _bool(a24.wr1),
                "wr2": _bool(a24.wr2),
                "nyt": _bool(a24.nyt),
                "fnl": _bool(a24.fnl),
            }

        s25 = self.session.get(UserS25Model, isu)
        if s25:
            met["s25"] = {
                "tsp": int(s25.tsp),
                "nck": s25.nck,
                "wr1": _bool(s25.wr1),
                "rr1": int(s25.rr1),
                "wr2": _bool(s25.wr2),
                "rr2": int(s25.rr2),
                "fnl": int(s25.fnl),
            }

        y25 = self.session.get(UserY25Model, isu)
        if y25:
            met["y25"] = {
                "tsp": int(y25.tsp),
                "nck": y25.nck,
                "nmb": y25.nmb,
                "bed": _bool(y25.bed),
                "way": int(y25.way),
                "car": y25.car,
                "liv": y25.liv,
                "ugo": int(y25.ugo),
            }

        a25 = self.session.get(UserA25Model, isu)
        if a25:
            met["a25"] = {
                "fio": a25.fio,
                "sts": _bool(a25.sts),
                "uid": int(a25.uid),
                "nck": a25.nck,
                "cmd": a25.cmd,
                "cid": int(a25.cid),
                "wr1": _bool(a25.wr1),
                "wr2": _bool(a25.wr2),
                "wr3": _bool(a25.wr3),
                "brs": _bool(a25.brs),
            }

        return UserDTO(isu=u.isu, uid=u.uid, fio=u.fio, grp=u.grp, nck=u.nck, met=met)

    def get_isu_by_uid(self, uid: int) -> int | None:
        row = self.session.execute(select(UserModel.isu).where(UserModel.uid == uid)).scalar_one_or_none()
        return int(row) if row is not None else None

    def upsert(self, dto: UserDTO) -> None:
        """
        Upserts base user fields. For event tables:
        - if dto.met contains event -> upsert corresponding row
        - if dto.met does NOT contain event -> delete corresponding row (keeps state consistent)

        IMPORTANT: we flush() right after inserting/updating base users row so that
        FK inserts into event tables work within the same transaction.
        """
        u = self.session.get(UserModel, dto.isu)
        if u is None:
            u = UserModel(isu=dto.isu, uid=dto.uid, fio=dto.fio or "", grp=dto.grp or "", nck=dto.nck or "")
            self.session.add(u)
        else:
            u.uid = dto.uid
            u.fio = dto.fio or ""
            u.grp = dto.grp or ""
            u.nck = dto.nck or ""

        # Ensure parent row exists in DB before inserting child rows
        self.session.flush()

        met = dto.met or {}

        # a24
        if "a24" in met:
            m = met["a24"] or {}
            row = self.session.get(UserA24Model, dto.isu)
            if row is None:
                row = UserA24Model(isu=dto.isu)
                self.session.add(row)
            row.tsp = int(m.get("tsp", 0) or 0)
            row.nck = str(m.get("nck", "") or "")
            row.lr1 = bool(m.get("lr1", False))
            row.wr1 = bool(m.get("wr1", False))
            row.wr2 = bool(m.get("wr2", False))
            row.nyt = bool(m.get("nyt", False))
            row.fnl = bool(m.get("fnl", False))
        else:
            self.session.execute(delete(UserA24Model).where(UserA24Model.isu == dto.isu))

        # s25
        if "s25" in met:
            m = met["s25"] or {}
            row = self.session.get(UserS25Model, dto.isu)
            if row is None:
                row = UserS25Model(isu=dto.isu)
                self.session.add(row)
            row.tsp = int(m.get("tsp", 0) or 0)
            row.nck = str(m.get("nck", "") or "")
            row.wr1 = bool(m.get("wr1", False))
            row.rr1 = int(m.get("rr1", 0) or 0)
            row.wr2 = bool(m.get("wr2", False))
            row.rr2 = int(m.get("rr2", 0) or 0)
            row.fnl = int(m.get("fnl", 0) or 0)
        else:
            self.session.execute(delete(UserS25Model).where(UserS25Model.isu == dto.isu))

        # y25
        if "y25" in met:
            m = met["y25"] or {}
            row = self.session.get(UserY25Model, dto.isu)
            if row is None:
                row = UserY25Model(isu=dto.isu)
                self.session.add(row)
            row.tsp = int(m.get("tsp", 0) or 0)
            row.nck = str(m.get("nck", "") or "")
            row.nmb = str(m.get("nmb", "") or "")
            row.bed = bool(m.get("bed", False))
            row.way = int(m.get("way", 0) or 0)
            row.car = str(m.get("car", "") or "")
            row.liv = str(m.get("liv", "") or "")
            row.ugo = int(m.get("ugo", 0) or 0)
        else:
            self.session.execute(delete(UserY25Model).where(UserY25Model.isu == dto.isu))

        # a25
        if "a25" in met:
            m = met["a25"] or {}
            row = self.session.get(UserA25Model, dto.isu)
            if row is None:
                row = UserA25Model(isu=dto.isu)
                self.session.add(row)
            row.fio = str(m.get("fio", "") or "")
            row.sts = bool(m.get("sts", False))
            row.uid = int(m.get("uid", 0) or 0)
            row.nck = str(m.get("nck", "") or "")
            row.cmd = str(m.get("cmd", "") or "")
            row.cid = int(m.get("cid", 0) or 0)
            row.wr1 = bool(m.get("wr1", False))
            row.wr2 = bool(m.get("wr2", False))
            row.wr3 = bool(m.get("wr3", False))
            row.brs = bool(m.get("brs", False))
        else:
            self.session.execute(delete(UserA25Model).where(UserA25Model.isu == dto.isu))

    def _special_isu_taken(self) -> set[int]:
        """
        special_isu = any isu outside [100000..999999].
        Need minimal free >=0 (legacy behavior).
        """
        rows = self.session.execute(
            select(UserModel.isu).where(and_(UserModel.isu < 100000, UserModel.isu >= 0))
        ).scalars().all()
        return set(int(x) for x in rows)

    def _next_special_isu(self) -> int:
        taken = self._special_isu_taken()
        n = 0
        while n in taken:
            n += 1
        return n

    def add_with_auto_isu(
        self,
        uid: int,
        fio: str = "",
        grp: str = "",
        nck: str = "",
        met: dict[str, Any] | None = None,
    ) -> UserDTO:
        if met is None:
            met = {}
        isu = self._next_special_isu()
        dto = UserDTO(isu=isu, uid=uid, fio=fio, grp=grp, nck=nck, met=met)
        self.upsert(dto)
        return dto

    def list_all_isus(self) -> list[int]:
        return [int(x) for x in self.session.execute(select(UserModel.isu)).scalars().all()]


class IgnoredRepository:
    def __init__(self, session: Session):
        self.session = session

    def is_ignored(self, uid: int) -> bool:
        return self.session.get(IgnoredUserModel, uid) is not None

    def add(self, uid: int) -> bool:
        if self.is_ignored(uid):
            return False
        self.session.add(IgnoredUserModel(uid=uid))
        return True

    def remove(self, uid: int) -> bool:
        res = self.session.execute(delete(IgnoredUserModel).where(IgnoredUserModel.uid == uid))
        return (res.rowcount or 0) > 0

    def list_all(self) -> set[int]:
        return set(int(x) for x in self.session.execute(select(IgnoredUserModel.uid)).scalars().all())

    def clear(self) -> None:
        self.session.execute(delete(IgnoredUserModel))