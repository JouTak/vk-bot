from __future__ import annotations

from loguru import logger

from vkbot.domain.user import User
from vkbot.domain.rules import is_real_isu, is_valid_uid
from vkbot.infrastructure.db.repositories.user_repo import UserRepository


class UserService:
    """Бизнес-логика работы с юзерами."""

    def __init__(self, repo: UserRepository):
        self.repo = repo

    def ensure_user_exists(self, uid: int, fio: str = "") -> User:
        """
        Вызывается на КАЖДОЕ входящее сообщение из ЛС.
        Гарантирует что юзер есть в базе.
        """
        existing = self.repo.get_by_uid(uid)
        if existing:
            return existing

        user = self.repo.add_with_auto_isu(uid=uid, fio=fio)
        logger.info(f"Auto-added new user: uid={uid}, isu={user.isu}")
        return user

    def merge_injection_data(
            self,
            isu: int | None,
            uid: int,
            fio: str,
            grp: str,
            nck: str,
            event_key: str,
            event_data: dict,
    ) -> User:
        """
        Инъекция данных из внешнего источника (Google Sheets, events.itmo.ru).

        Правила:
        - Если ISU настоящий (100000–999999) и есть в базе → обновить по ISU
        - Если ISU специальный/отсутствует → искать по VK UID
        - Если VK UID совпадает → обновить базовые поля
        - Данные ивента всегда добавляются/обновляются
        """
        user = None

        # 1. Ищем по настоящему ISU
        if isu is not None and is_real_isu(isu):
            user = self.repo.get_by_isu(isu)

        # 2. Если не нашли — ищем по VK UID
        if user is None and is_valid_uid(uid):
            user = self.repo.get_by_uid(uid)

        # 3. Если не нашли — создаём нового
        if user is None:
            new_isu = isu if isu is not None else self.repo.next_special_isu()
            user = User(isu=new_isu, uid=uid, fio=fio, grp=grp, nck=nck)

        # Обновляем базовые поля если новые данные лучше
        if fio and not user.fio:
            user.fio = fio
        elif fio and user.has_real_isu:
            # Для настоящих ISU всегда обновляем fio из инъекции
            user.fio = fio

        if grp and not user.grp:
            user.grp = grp

        if nck and not user.nck:
            user.nck = nck

        if is_valid_uid(uid) and not is_valid_uid(user.uid):
            user.uid = uid

        # Добавляем/обновляем данные ивента
        user.met[event_key] = event_data

        return self.repo.upsert(user)
