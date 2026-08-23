from __future__ import annotations

from typing import Any

from sqlalchemy import select, and_
from sqlalchemy.orm import Session

from vkbot.domain.user import User
from ..models import UserModel, EVENT_MODELS
from ..event_registry import get_event


class UserRepository:
    def __init__(self, session: Session):
        self.session = session

    # ----------------------------------------------------------
    # READ
    # ----------------------------------------------------------

    def get_by_isu(self, isu: int) -> User | None:
        row = self.session.execute(
            select(UserModel).where(UserModel.isu == isu)
        ).scalar_one_or_none()
        if not row:
            return None
        return self._to_domain(row)

    def get_by_uid(self, uid: int) -> User | None:
        row = self.session.execute(
            select(UserModel).where(UserModel.uid == uid)
        ).scalar_one_or_none()
        if not row:
            return None
        return self._to_domain(row)

    def _to_domain(self, row: UserModel) -> User:
        """Собирает доменный User из ORM + все данные ивентов."""
        met: dict[str, dict[str, Any]] = {}

        # Генеричный сбор данных по всем зарегистрированным ивентам
        for event_key, model_cls in EVENT_MODELS.items():
            event_row = self.session.get(model_cls, row.isu)
            if event_row is None:
                continue

            event_def = get_event(event_key)
            if event_def is None:
                continue

            data = {}
            for field_def in event_def.fields:
                data[field_def.name] = getattr(event_row, field_def.name, field_def.default)
            met[event_key] = data

        return User(
            isu=row.isu,
            uid=row.uid,
            fio=row.fio,
            grp=row.grp,
            nck=row.nck,
            met=met,
        )

    # ----------------------------------------------------------
    # WRITE
    # ----------------------------------------------------------

    def change_isu(self, old_isu: int, new_isu: int) -> bool:
        """Перенос юзера на новый ISU вместе со всеми ивент-строками."""
        if old_isu == new_isu:
            return False

        old_row = self.session.get(UserModel, old_isu)
        if old_row is None:
            return False
        if self.session.get(UserModel, new_isu) is not None:
            return False  # целевой ISU уже занят — не трогаем

        new_row = UserModel(
            isu=new_isu,
            uid=old_row.uid,
            fio=old_row.fio,
            grp=old_row.grp,
            nck=old_row.nck,
        )
        self.session.add(new_row)
        self.session.flush()  # FK на users.isu должен существовать

        # Переносим строки ивентов
        for model_cls in EVENT_MODELS.values():
            ev_row = self.session.get(model_cls, old_isu)
            if ev_row is not None:
                ev_row.isu = new_isu
        self.session.flush()

        self.session.delete(old_row)
        self.session.flush()
        return True

    def upsert(self, user: User, merge_events: bool = True) -> User:
        """Создать или обновить юзера + все его ивенты."""
        # 1. Базовая запись
        row = self.session.get(UserModel, user.isu)
        if row is None:
            row = UserModel(isu=user.isu)
            self.session.add(row)

        row.uid = user.uid
        row.fio = user.fio
        row.grp = user.grp
        row.nck = user.nck
        self.session.flush()

        # 2. Ивенты — генерично, без if/elif
        for event_key, event_data in user.met.items():
            event_def = get_event(event_key)
            if event_def is None:
                continue  # неизвестный ивент — пропускаем

            model_cls = EVENT_MODELS.get(event_key)
            if model_cls is None:
                continue

            event_row = self.session.get(model_cls, user.isu)
            if event_row is None:
                event_row = model_cls(isu=user.isu)
                self.session.add(event_row)

            # Заполняем поля из декларации
            for field_def in event_def.fields:
                raw_value = event_data.get(field_def.name, field_def.default)
                coerced = self._coerce(raw_value, field_def.type)
                setattr(event_row, field_def.name, coerced)

        return user

    def add_with_auto_isu(
            self,
            uid: int,
            fio: str = "",
            grp: str = "",
            nck: str = "",
            met: dict[str, Any] | None = None,
    ) -> User:
        """Создать юзера с автогенерируемым ISU (для внешних)."""
        new_isu = self.next_special_isu()
        user = User(isu=new_isu, uid=uid, fio=fio, grp=grp, nck=nck, met=met or {})
        return self.upsert(user)

    # ----------------------------------------------------------
    # HELPERS
    # ----------------------------------------------------------

    def list_all_users(self) -> list[User]:
        """Все юзеры + их ивенты за 1 + len(events) запросов."""
        rows = self.session.execute(select(UserModel)).scalars().all()

        event_rows: dict[str, dict[int, object]] = {}
        for event_key, model_cls in EVENT_MODELS.items():
            ev_rows = self.session.execute(select(model_cls)).scalars().all()
            event_rows[event_key] = {r.isu: r for r in ev_rows}

        users = []
        for row in rows:
            met: dict[str, dict[str, Any]] = {}
            for event_key, by_isu in event_rows.items():
                ev_row = by_isu.get(row.isu)
                if ev_row is None:
                    continue
                event_def = get_event(event_key)
                if event_def is None:
                    continue
                met[event_key] = {
                    f.name: getattr(ev_row, f.name, f.default)
                    for f in event_def.fields
                }
            users.append(User(
                isu=row.isu, uid=row.uid, fio=row.fio, grp=row.grp, nck=row.nck, met=met,
            ))
        return users

    def next_special_isu(self) -> int:
        rows = self.session.execute(
            select(UserModel.isu).where(
                and_(UserModel.isu >= 0, UserModel.isu < 100000)
            )
        ).scalars().all()
        taken = set(int(x) for x in rows)
        n = 0
        while n in taken:
            n += 1
        return n

    @staticmethod
    def _coerce(value: Any, field_type: str) -> Any:
        """Приводит значение к типу поля."""
        if field_type == "int":
            try:
                return int(value) if value is not None else 0
            except (TypeError, ValueError):
                return 0
        elif field_type == "bool":
            if isinstance(value, bool):
                return value
            if isinstance(value, (int, float)):
                return bool(int(value))
            if isinstance(value, str):
                return value.strip().lower() in ("1", "true", "yes", "да", "y")
            return bool(value)
        elif field_type == "str":
            return str(value) if value is not None else ""
        return value
