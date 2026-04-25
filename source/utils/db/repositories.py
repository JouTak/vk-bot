from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from sqlalchemy import and_, delete, select
from sqlalchemy.orm import Session

from .models import (
    IgnoredUserModel,
    UserA24Model,
    UserA25Model,
    UserEventModel,
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


def _to_int(v: Any, default: int = 0) -> int:
    try:
        if v is None:
            return default
        if isinstance(v, bool):
            return int(v)
        if isinstance(v, (int, float)):
            return int(v)
        if isinstance(v, str) and v.strip().lstrip("-").isdigit():
            return int(v.strip())
    except Exception:
        pass
    return default


def _to_bool(v: Any, default: bool = False) -> bool:
    if isinstance(v, bool):
        return v
    if isinstance(v, (int, float)):
        return bool(int(v))
    if isinstance(v, str):
        value = v.strip().lower()
        if value in {"1", "true", "yes", "y", "on", "да"}:
            return True
        if value in {"0", "false", "no", "n", "off", "нет"}:
            return False
    return default


KNOWN_EVENT_KEYS = {"a24", "s25", "y25", "a25"}
LEGACY_EVENT_KEY_ALIASES = {"s24": "a24"}


def _canonical_event_key(key: str) -> str:
    return LEGACY_EVENT_KEY_ALIASES.get(key, key)


def _canonicalize_met(met: dict[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in (met or {}).items():
        if not isinstance(key, str):
            continue
        canonical = _canonical_event_key(key)
        if canonical not in result:
            result[canonical] = value
    return result


class UserRepository:
    def __init__(self, session: Session):
        self.session = session

    def get(self, isu: int) -> UserDTO | None:
        u = self.session.get(UserModel, isu)
        if not u:
            return None

        met: dict[str, Any] = {}

        generic_events = self.session.execute(
            select(UserEventModel).where(UserEventModel.isu == isu)
        ).scalars().all()
        for event in generic_events:
            try:
                parsed = json.loads(event.data_json) if event.data_json else {}
            except Exception:
                parsed = {}
            met[_canonical_event_key(event.event_key)] = parsed

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

    def _upsert_a24(self, isu: int, value: Any) -> None:
        m = value if isinstance(value, dict) else {}
        row = self.session.get(UserA24Model, isu)
        if row is None:
            row = UserA24Model(isu=isu)
            self.session.add(row)
        row.tsp = _to_int(m.get("tsp", 0))
        row.nck = str(m.get("nck", "") or "")
        row.lr1 = _to_bool(m.get("lr1", False))
        row.wr1 = _to_bool(m.get("wr1", False))
        row.wr2 = _to_bool(m.get("wr2", False))
        row.nyt = _to_bool(m.get("nyt", False))
        row.fnl = _to_bool(m.get("fnl", False))

    def migrate_legacy_event_aliases(self) -> int:
        migrated = 0
        for legacy_key, canonical_key in LEGACY_EVENT_KEY_ALIASES.items():
            if canonical_key != "a24":
                continue
            rows = self.session.execute(
                select(UserEventModel).where(UserEventModel.event_key == legacy_key)
            ).scalars().all()
            for row in rows:
                try:
                    data = json.loads(row.data_json) if row.data_json else {}
                except Exception:
                    data = {}
                self._upsert_a24(row.isu, data)
                self.session.delete(row)
                migrated += 1
        return migrated

    def upsert(
        self,
        dto: UserDTO,
        *,
        merge_events: bool = True,
        preserve_existing_base_if_has_a25: bool = True,
    ) -> None:
        raw_met = dto.met or {}
        met = _canonicalize_met(raw_met)
        legacy_alias_keys = [key for key in raw_met.keys() if isinstance(key, str) and _canonical_event_key(key) != key]
        u = self.session.get(UserModel, dto.isu)
        has_existing_a25 = self.session.get(UserA25Model, dto.isu) is not None

        if u is None:
            u = UserModel(isu=dto.isu, uid=dto.uid, fio=dto.fio or "", grp=dto.grp or "", nck=dto.nck or "")
            self.session.add(u)
        elif not (preserve_existing_base_if_has_a25 and has_existing_a25 and "a25" not in met):
            u.uid = dto.uid
            u.fio = dto.fio or ""
            u.grp = dto.grp or ""
            u.nck = dto.nck or ""

        self.session.flush()

        if "a24" in met:
            self._upsert_a24(dto.isu, met["a24"])
        elif not merge_events:
            self.session.execute(delete(UserA24Model).where(UserA24Model.isu == dto.isu))

        if "s25" in met:
            m = met["s25"] or {}
            row = self.session.get(UserS25Model, dto.isu)
            if row is None:
                row = UserS25Model(isu=dto.isu)
                self.session.add(row)
            row.tsp = _to_int(m.get("tsp", 0))
            row.nck = str(m.get("nck", "") or "")
            row.wr1 = _to_bool(m.get("wr1", False))
            row.rr1 = _to_int(m.get("rr1", 0))
            row.wr2 = _to_bool(m.get("wr2", False))
            row.rr2 = _to_int(m.get("rr2", 0))
            row.fnl = _to_int(m.get("fnl", 0))
        elif not merge_events:
            self.session.execute(delete(UserS25Model).where(UserS25Model.isu == dto.isu))

        if "y25" in met:
            m = met["y25"] or {}
            row = self.session.get(UserY25Model, dto.isu)
            if row is None:
                row = UserY25Model(isu=dto.isu)
                self.session.add(row)
            row.tsp = _to_int(m.get("tsp", 0))
            row.nck = str(m.get("nck", "") or "")
            row.nmb = str(m.get("nmb", "") or "")
            row.bed = _to_bool(m.get("bed", False))
            row.way = _to_int(m.get("way", 0))
            row.car = str(m.get("car", "") or "")
            row.liv = str(m.get("liv", "") or "")
            row.ugo = _to_int(m.get("ugo", 0))
        elif not merge_events:
            self.session.execute(delete(UserY25Model).where(UserY25Model.isu == dto.isu))

        if "a25" in met:
            m = met["a25"] or {}
            row = self.session.get(UserA25Model, dto.isu)
            if row is None:
                row = UserA25Model(isu=dto.isu)
                self.session.add(row)
            row.fio = str(m.get("fio", "") or "")
            row.sts = _to_bool(m.get("sts", False))
            row.uid = _to_int(m.get("uid", 0))
            row.nck = str(m.get("nck", "") or "")
            row.cmd = str(m.get("cmd", "") or "")
            row.cid = _to_int(m.get("cid", 0))
            row.wr1 = _to_bool(m.get("wr1", False))
            row.wr2 = _to_bool(m.get("wr2", False))
            row.wr3 = _to_bool(m.get("wr3", False))
            row.brs = _to_bool(m.get("brs", False))
        elif not merge_events:
            self.session.execute(delete(UserA25Model).where(UserA25Model.isu == dto.isu))

        for legacy_key in legacy_alias_keys:
            self.session.execute(
                delete(UserEventModel).where(
                    UserEventModel.isu == dto.isu,
                    UserEventModel.event_key == legacy_key,
                )
            )

        generic_keys: set[str] = set()
        for key, value in met.items():
            if not isinstance(key, str) or key in KNOWN_EVENT_KEYS or not key or len(key) > 128:
                continue
            generic_keys.add(key)
            row = self.session.get(UserEventModel, (dto.isu, key))
            if row is None:
                row = UserEventModel(isu=dto.isu, event_key=key)
                self.session.add(row)
            row.data_json = json.dumps(value if value is not None else {}, ensure_ascii=False)

        if not merge_events:
            self.session.execute(
                delete(UserEventModel).where(
                    UserEventModel.isu == dto.isu,
                    UserEventModel.event_key.not_in(generic_keys),
                )
            )

    def _special_isu_taken(self) -> set[int]:
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
