from __future__ import annotations

from loguru import logger
from sqlalchemy.exc import IntegrityError

from vkbot.domain.user import User
from vkbot.domain.rules import is_real_isu, is_valid_uid
from vkbot.infrastructure.db.repositories.user_repo import UserRepository


class UserService:
    """Бизнес-логика работы с юзерами."""

    def __init__(self, repo: UserRepository):
        """Сохраняет репозиторий пользователей."""
        self.repo = repo

    def ensure_user_exists(self, uid: int, fio: str = "") -> None:
        """
        Вызывается на каждое входящее сообщение из ЛС.
        Гарантирует, что юзер есть в базе.
        """
        if self.repo.exists_by_uid(uid):
            return

        try:
            user = self.repo.add_with_auto_isu(uid=uid, fio=fio)
            logger.info(f"Auto-added new user: uid={uid}, isu={user.isu}")
        except IntegrityError:
            self.repo.session.rollback()

            if self.repo.exists_by_uid(uid):
                return

            raise

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
        """Сливает данные инъекции ивента с существующим пользователем или создаёт нового."""
        user = None

        # 1) Поиск по настоящему ISU
        if isu is not None and is_real_isu(isu):
            user = self.repo.get_by_isu(isu)

        # 2) Поиск по VK UID
        if user is None and is_valid_uid(uid):
            found = self.repo.get_by_uid(uid)
            if found is not None:
                if (
                        isu is not None
                        and is_real_isu(isu)
                        and not found.has_real_isu
                ):
                    if self.repo.change_isu(found.isu, isu):
                        found = self.repo.get_by_isu(isu)
                user = found

        # 3) Новый юзер
        if user is None:
            new_isu = (
                isu if (isu is not None and is_real_isu(isu))
                else self.repo.next_special_isu()
            )
            user = User(isu=new_isu, uid=uid if uid else 0)

        if is_valid_uid(uid):
            user.uid = uid
        if fio:
            user.fio = fio
        if grp:
            user.grp = grp
        if nck:
            user.nck = nck

        user.met[event_key] = event_data

        return self.repo.upsert(user)
