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
        new_isu = self._next_special_isu()
        user = User(isu=new_isu, uid=uid, fio=fio, grp=grp, nck=nck, met=met or {})
        return self.upsert(user)

    # ----------------------------------------------------------
    # HELPERS
    # ----------------------------------------------------------

    def list_all_uids(self) -> dict[int, int]:
        """uid -> isu mapping для всех валидных юзеров."""
        rows = self.session.execute(
            select(UserModel.uid, UserModel.isu).where(UserModel.uid > 1)
        ).all()
        return {int(uid): int(isu) for uid, isu in rows}

    def _next_special_isu(self) -> int:
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
