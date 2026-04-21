from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

from ..db.db import is_database_enabled, session_scope
from ..db.repositories import UserRepository, UserDTO
from ..db.models import UsersRawLineModel


def s2t(s: str) -> int:
    return int(datetime.strptime(s, "%m/%d/%Y %H:%M:%S").timestamp())


def t2s(timestamp: int) -> str:
    return datetime.fromtimestamp(timestamp).strftime("%m/%d/%Y %H:%M:%S")


class User:
    info_type = tuple[int, int, str, str, str, dict[str, dict[str, str | int | bool]]]
    s2b = staticmethod(lambda s: s == "1")
    text2info = (
        int,
        int,
        str,
        str,
        str,
        {
            "a24": {"tsp": int, "nck": str, "lr1": s2b, "wr1": s2b, "wr2": s2b, "nyt": s2b, "fnl": s2b},
            "s25": {"tsp": int, "nck": str, "wr1": s2b, "rr1": str, "wr2": s2b, "rr2": str, "fnl": str},
            "y25": {"tsp": int, "nck": str, "nmb": str, "bed": s2b, "way": int, "car": str, "liv": str, "ugo": int},
            "a25": {
                "fio": str,
                "sts": s2b,
                "uid": int,
                "nck": str,
                "cmd": str,
                "cid": int,
                "wr1": s2b,
                "wr2": s2b,
                "wr3": s2b,
                "brs": s2b,
            },
        },
    )
    t2ic = staticmethod(str.isdigit)
    t2bc = staticmethod(["0", "1"].__contains__)
    text2info_check = (
        t2ic,
        t2ic,
        bool,
        bool,
        bool,
        {
            "a24": {"tsp": t2ic, "nck": bool, "lr1": t2bc, "wr1": t2bc, "wr2": t2bc, "nyt": t2bc, "fnl": t2bc},
            "s25": {"tsp": t2ic, "nck": bool, "wr1": t2bc, "rr1": t2ic, "wr2": t2bc, "rr2": t2ic, "fnl": t2ic},
            "y25": {"tsp": t2ic, "nck": bool, "nmb": bool, "bed": t2bc, "way": t2ic, "car": bool, "liv": bool, "ugo": t2ic},
            "a25": {
                "fio": bool,
                "sts": t2bc,
                "uid": t2ic,
                "nck": bool,
                "cmd": bool,
                "cid": t2ic,
                "wr1": t2bc,
                "wr2": t2bc,
                "wr3": t2bc,
                "brs": t2bc,
            },
        },
    )
    b2t = staticmethod(lambda b: "Да" if b else "Нет")
    w2t = staticmethod(
        ("На бесплатном трансфере от ГК", "Своим ходом (электричка)", "Своим ходом (на машине)").__getitem__
    )
    opt = staticmethod(lambda x: x if (x and x != "-") else "[НЕТ ДАННЫХ]")
    u2t = staticmethod(("Нет.", "Да, ты прошёл отбор, ждём оплату!", "Оплата дошла до нас, ты едешь!").__getitem__)
    info2text = (
        str,
        str,
        str,
        str,
        str,
        {
            "a24": {"tsp": t2s, "nck": opt, "lr1": b2t, "wr1": b2t, "wr2": b2t, "nyt": b2t, "fnl": b2t},
            "s25": {"tsp": t2s, "nck": opt, "wr1": b2t, "rr1": opt, "wr2": b2t, "rr2": opt, "fnl": opt},
            "y25": {"tsp": t2s, "nck": opt, "nmb": opt, "bed": b2t, "way": w2t, "car": opt, "liv": opt, "ugo": u2t},
            "a25": {
                "fio": opt,
                "sts": b2t,
                "uid": opt,
                "nck": opt,
                "cmd": opt,
                "cid": opt,
                "wr1": b2t,
                "wr2": b2t,
                "wr3": b2t,
                "brs": b2t,
            },
        },
    )
    db2save = (str, str, str, str, str, lambda x: json.dumps(x, ensure_ascii=False))
    keys = ("isu", "uid", "fio", "grp", "nck", "met")
    flat_i2t: dict[str, Any] = {}

    def __init__(self, info: info_type) -> None:
        self.info = info

    def __getitem__(self, key: str):
        return self.info[User.keys.index(key)] if key in User.keys else None

    def __getattribute__(self, key: str):
        return super().__getattribute__(key) if key == "info" else (
            self.info[User.keys.index(key)] if key in User.keys else None
        )


class UserList:
    def __init__(self, path: str, vk_helper) -> None:
        self.vk_helper = vk_helper
        self.uid_to_isu: dict[int, int] = {}
        self._loaded = False
        self._db_enabled = is_database_enabled()
        self.path = path or os.getenv("USERS_TXT_PATH", "./subscribers/users.txt")
        self.db: dict[int, User] = {}
        self.errors: list[tuple[str, ...]] = []
        self.max_special_isu = 0
        self.used_specials_isus: set[int] = set()
        self.load()

    def load(self) -> bool:
        if self._db_enabled:
            with session_scope() as s:
                repo = UserRepository(s)
                isus = repo.list_all_isus()
                self.uid_to_isu = {}
                for isu in isus:
                    user = repo.get(isu)
                    if user and not (0 <= int(user.uid) <= 1):
                        self.uid_to_isu[int(user.uid)] = int(isu)
            self._loaded = True
            return True

        path = Path(self.path)
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            path.write_text("", encoding="utf-8")

        self.db.clear()
        self.errors.clear()
        self.uid_to_isu.clear()
        self.used_specials_isus.clear()
        self.max_special_isu = 0

        for raw_line in path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line:
                continue
            parts = raw_line.split("\t")
            if len(parts) != 6:
                self.errors.append(tuple(parts))
                continue
            try:
                isu = int(parts[0])
                uid = int(parts[1])
                met = json.loads(parts[5]) if parts[5] else {}
                if not isinstance(met, dict):
                    raise ValueError("met is not dict")
            except Exception:
                self.errors.append(tuple(parts))
                continue

            if not 100000 <= isu <= 999999:
                self.used_specials_isus.add(isu)

            user = User((isu, uid, parts[2], parts[3], parts[4], met))
            self.db[isu] = user
            if not (0 <= uid <= 1):
                self.uid_to_isu[uid] = isu

        self._loaded = True
        return True

    def save(self) -> bool:
        if self._db_enabled:
            return True

        path = Path(self.path)
        path.parent.mkdir(parents=True, exist_ok=True)
        to_save = []
        for isu in self.db.keys():
            to_save.append("\t".join(f(i) for f, i in zip(User.db2save, self.db[isu].info)))
        to_save.extend("\t".join(parts) for parts in self.errors if parts)
        to_save.sort(key=lambda x: int(x.split("\t")[0]) if x.split("\t")[0].lstrip("-").isdigit() else -1)
        path.write_text("\n".join([i for i in to_save if i and i[0] != "0"]), encoding="utf-8")
        return True

    def keys(self):
        if self._db_enabled:
            with session_scope() as s:
                repo = UserRepository(s)
                return repo.list_all_isus()
        return self.db.keys()

    def get(self, isu: int) -> User | None:
        if self._db_enabled:
            with session_scope() as s:
                repo = UserRepository(s)
                dto = repo.get(isu)
                if not dto:
                    return None
                return User((dto.isu, dto.uid, dto.fio, dto.grp, dto.nck, dto.met))
        return self.db[isu] if isu in self.db else None

    def add(self, info: User.info_type) -> User:
        if self._db_enabled:
            isu, uid, fio, grp, nck, met = info
            with session_scope() as s:
                repo = UserRepository(s)
                if isu == -1:
                    dto = repo.add_with_auto_isu(uid=int(uid), fio=fio, grp=grp, nck=nck, met=met or {})
                else:
                    dto = UserDTO(isu=int(isu), uid=int(uid), fio=fio or "", grp=grp or "", nck=nck or "", met=met or {})
                    repo.upsert(dto)
                if not (0 <= int(dto.uid) <= 1):
                    self.uid_to_isu[int(dto.uid)] = int(dto.isu)
                return User((dto.isu, dto.uid, dto.fio, dto.grp, dto.nck, dto.met))

        if info[0] == -1:
            info = tuple([self.get_new_special_isu()] + list(info[1:]))
        user = User(info)
        self.db[info[0]] = user
        if not (0 <= info[1] <= 1):
            self.uid_to_isu[info[1]] = info[0]
        return user

    def get_new_special_isu(self) -> int:
        while self.max_special_isu in self.used_specials_isus:
            self.max_special_isu += 1
        self.used_specials_isus.add(self.max_special_isu)
        return self.max_special_isu


def import_users_txt_to_db(users_txt_path: str) -> int:
    imported = 0

    with open(users_txt_path, "r", encoding="UTF-8") as f:
        lines = [ln.rstrip("\n") for ln in f.readlines() if ln.strip()]

    for line_no, raw in enumerate(lines, start=1):
        parts = raw.split("\t")

        parsed_isu: int | None = None
        parsed_uid: int | None = None
        parsed_fio = ""
        parsed_grp = ""
        parsed_nck = ""
        parsed_met_json = ""
        err = ""

        if len(parts) == 6:
            if parts[0].isdigit():
                parsed_isu = int(parts[0])
            if parts[1].lstrip("-").isdigit():
                parsed_uid = int(parts[1])
            parsed_fio = parts[2] or ""
            parsed_grp = parts[3] or ""
            parsed_nck = parts[4] or ""
            parsed_met_json = parts[5] or ""
        else:
            err = f"bad_columns:{len(parts)}"

        try:
            isu = int(parts[0]) if len(parts) > 0 and parts[0].isdigit() else None
            uid = int(parts[1]) if len(parts) > 1 and parts[1].lstrip("-").isdigit() else None
            if len(parts) != 6:
                raise ValueError(f"bad_columns:{len(parts)}")
            if isu is None:
                raise ValueError("isu_not_int")
            if uid is None:
                raise ValueError("uid_not_int")

            soft_issues: list[str] = []

            if 0 <= int(uid) <= 1:
                soft_issues.append("uid_invalid_0_1")

            grp = (parts[3] or "").strip()
            if grp:
                if len(grp) != 5 or not ("A" <= grp[0] <= "Z") or not grp[1:].isdigit():
                    soft_issues.append("grp_invalid_format")

            nck = (parts[4] or "").strip()
            if nck:
                if " " in nck:
                    soft_issues.append("nck_invalid_format")
                else:
                    for ch in nck:
                        if not (("a" <= ch.lower() <= "z") or ("0" <= ch <= "9") or ch == "_"):
                            soft_issues.append("nck_invalid_format")
                            break
            if len(nck) > 64:
                soft_issues.append("nck_too_long")

            met = json.loads(parts[5]) if parts[5] else {}

            def to_int(v, default=0):
                try:
                    if v is None:
                        return default
                    if isinstance(v, bool):
                        return int(v)
                    if isinstance(v, (int, float)):
                        return int(v)
                    if isinstance(v, str) and v.strip().lstrip("-").isdigit():
                        return int(v)
                except Exception:
                    pass
                return default

            def to_bool(v, default=False):
                if isinstance(v, bool):
                    return v
                if isinstance(v, (int, float)):
                    return bool(int(v))
                if isinstance(v, str):
                    if v in ("1", "true", "True", "да", "Да"):
                        return True
                    if v in ("0", "false", "False", "нет", "Нет"):
                        return False
                return default

            for key in ("a24", "s25", "y25", "a25"):
                if key not in met or not isinstance(met.get(key), dict):
                    continue
                m = met[key]

                if key in ("a24", "s25", "y25"):
                    if "tsp" in m:
                        m["tsp"] = to_int(m.get("tsp", 0))
                    if key == "a24":
                        for b in ("lr1", "wr1", "wr2", "nyt", "fnl"):
                            if b in m:
                                m[b] = to_bool(m.get(b, False))
                    if key == "s25":
                        for i in ("rr1", "rr2", "fnl"):
                            if i in m:
                                m[i] = to_int(m.get(i, 0))
                        if "wr1" in m:
                            m["wr1"] = to_bool(m.get("wr1", False))
                        if "wr2" in m:
                            m["wr2"] = to_bool(m.get("wr2", False))
                    if key == "y25":
                        for i in ("way", "ugo"):
                            if i in m:
                                m[i] = to_int(m.get(i, 0))
                        if "bed" in m:
                            m["bed"] = to_bool(m.get("bed", False))

                if key == "a25":
                    for i in ("uid", "cid"):
                        if i in m:
                            m[i] = to_int(m.get(i, 0))
                    for b in ("sts", "wr1", "wr2", "wr3", "brs"):
                        if b in m:
                            m[b] = to_bool(m.get(b, False))

            dto = UserDTO(
                isu=isu,
                uid=uid,
                fio=parts[2] or "",
                grp=parts[3] or "",
                nck=parts[4] or "",
                met=met,
            )

            with session_scope() as s:
                repo = UserRepository(s)
                repo.upsert(dto)

            imported += 1

            if soft_issues:
                err = soft_issues[0]
                with session_scope() as s:
                    raw_row = (
                        s.query(UsersRawLineModel)
                        .filter(UsersRawLineModel.line_no == line_no, UsersRawLineModel.raw_line == raw)
                        .order_by(UsersRawLineModel.id.desc())
                        .first()
                    )
                    if raw_row is None:
                        raw_row = UsersRawLineModel(line_no=line_no, raw_line=raw)
                        s.add(raw_row)

                    raw_row.isu = parsed_isu
                    raw_row.uid = parsed_uid
                    raw_row.fio = parsed_fio
                    raw_row.grp = parsed_grp
                    raw_row.nck = parsed_nck
                    raw_row.met_json = parsed_met_json
                    raw_row.status = "skipped"
                    raw_row.error = err

            continue
        except Exception as e:
            err = str(e)

        with session_scope() as s:
            raw_row = (
                s.query(UsersRawLineModel)
                .filter(UsersRawLineModel.line_no == line_no, UsersRawLineModel.raw_line == raw)
                .order_by(UsersRawLineModel.id.desc())
                .first()
            )
            if raw_row is None:
                raw_row = UsersRawLineModel(line_no=line_no, raw_line=raw)
                s.add(raw_row)

            raw_row.isu = parsed_isu
            raw_row.uid = parsed_uid
            raw_row.fio = parsed_fio
            raw_row.grp = parsed_grp
            raw_row.nck = parsed_nck
            raw_row.met_json = parsed_met_json
            raw_row.status = "error"
            raw_row.error = err

    return imported
