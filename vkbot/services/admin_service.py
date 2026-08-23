from __future__ import annotations

from loguru import logger
from sqlalchemy import text

from vkbot.domain.user import User
from vkbot.domain.permissions import PermissionChecker
from vkbot.infrastructure.db.engine import session_scope
from vkbot.infrastructure.db.repositories.user_repo import UserRepository
from vkbot.services.message_service import MessageService
from vkbot.services.condition_parser import (
    check_and_evaluate,
    validate_condition,
)


class AdminService:
    """Все админские команды."""

    def __init__(self, perms: PermissionChecker, vk_client, msg_svc: MessageService):
        self.perms = perms
        self.vk = vk_client
        self.msg_svc = msg_svc

    # ----------------------------------------------------------
    # sender
    # ----------------------------------------------------------

    def sender(self, admin_uid: int, condition: str, message: str) -> str:
        """Рассылка по условию."""
        if not self.perms.is_admin(admin_uid):
            return "Нет доступа"

        # Валидация
        errors = validate_condition(condition)
        if errors:
            return "Ошибки в условии:\n" + "\n".join(errors)

        # Загружаем всех юзеров
        users = self._load_all_users()

        # Фильтруем
        matched, eval_errors = check_and_evaluate(users, condition)
        if eval_errors:
            return "Ошибки:\n" + "\n".join(eval_errors)

        if not matched:
            return "Совпадений: 0. Никому не отправлено."

        # Форматируем и отправляем
        actions = []
        for user in matched:
            formatted = self._format_sender_message(message, user)
            actions.append({
                "peer_id": user.uid,
                "message": formatted,
            })

        # Отправка батчами
        results = self.vk.send_messages(actions)

        sent = sum(1 for r in results if r and not (isinstance(r, dict) and r.get("error")))
        failed = len(actions) - sent

        response = f"Отправлено: {sent}"
        if failed > 0:
            response += f"\nОшибок: {failed}"

        logger.info(f"[sender] condition='{condition}', sent={sent}, failed={failed}")
        return response

    # ----------------------------------------------------------
    # query
    # ----------------------------------------------------------

    def query(self, admin_uid: int, condition: str) -> str:
        """Показать юзеров по условию без отправки."""
        if not self.perms.is_admin(admin_uid):
            return "Нет доступа"

        errors = validate_condition(condition)
        if errors:
            return "Ошибки в условии:\n" + "\n".join(errors)

        users = self._load_all_users()
        matched, eval_errors = check_and_evaluate(users, condition)
        if eval_errors:
            return "Ошибки:\n" + "\n".join(eval_errors)

        if not matched:
            return "Совпадений: 0"

        lines = [f"Совпадений: {len(matched)}",
                 f"Первые {min(10, len(matched))}:"]

        for user in matched[:10]:
            nck = user.nck or "-"
            fio = user.fio or "-"
            lines.append(f"• {user.isu} | {user.uid} | {nck} | {fio}")

        return "\n".join(lines)

    # ----------------------------------------------------------
    # db (SQL console)
    # ----------------------------------------------------------

    def db_query(self, admin_uid: int, sql: str) -> str:
        """Выполнить SQL-запрос."""
        if not self.perms.is_admin(admin_uid):
            return "Нет доступа"

        if not sql.strip():
            return "Использование: db <SQL запрос>"

        try:
            with session_scope() as s:
                result = s.execute(text(sql))

                if sql.strip().upper().startswith("SELECT"):
                    rows = result.fetchall()
                    if not rows:
                        return "Пустой результат"

                    cols = result.keys()
                    header = " | ".join(str(c) for c in cols)
                    lines = [header, "-" * len(header)]

                    for row in rows[:50]:
                        lines.append(" | ".join(str(v) for v in row))

                    if len(rows) > 50:
                        lines.append(f"... и ещё {len(rows) - 50} строк")

                    output = "\n".join(lines)
                    if len(output) > 4000:
                        output = output[:4000] + "\n... (обрезано)"
                    return output
                else:
                    affected = result.rowcount
                    return f"OK. Затронуто строк: {affected}"

        except Exception as e:
            return f"Ошибка SQL: {e}"

    # ----------------------------------------------------------
    # reload
    # ----------------------------------------------------------

    def reload(self, admin_uid: int) -> str:
        """Перезагрузить инъекции."""
        if not self.perms.is_admin(admin_uid):
            return "Нет доступа"

        from vkbot.services.event_service import EventService
        from vkbot.services.user_service import UserService

        with session_scope() as s:
            repo = UserRepository(s)
            user_svc = UserService(repo)
            event_svc = EventService(user_svc, vk_client=self.vk)
            results = event_svc.inject_all_active()

        lines = []
        for key, stats in results.items():
            lines.append(
                f"{key}: source={stats.get('source')}, "
                f"upserted={stats.get('upserted')}, "
                f"skipped={stats.get('skipped')}"
            )
        return "\n".join(lines) if lines else "Нет активных ивентов для инъекции"

    # ----------------------------------------------------------
    # Хелперы
    # ----------------------------------------------------------

    def _load_all_users(self) -> list[User]:
        """Загружает всех юзеров из БД."""
        with session_scope() as s:
            repo = UserRepository(s)
            isus = repo.list_all_uids()  # uid -> isu
            users = []
            for uid, isu in isus.items():
                user = repo.get_by_isu(isu)
                if user:
                    users.append(user)
            return users

    def _format_sender_message(self, template: str, user: User) -> str:
        """Форматирует сообщение для рассылки с подстановкой полей юзера."""
        # Простая подстановка: {isu}, {uid}, {fio}, {grp}, {nck}
        # + met.<event>.<field>
        result = template
        result = result.replace("{isu}", str(user.isu))
        result = result.replace("{uid}", str(user.uid))
        result = result.replace("{fio}", user.fio or "")
        result = result.replace("{grp}", user.grp or "")
        result = result.replace("{nck}", user.nck or "")

        # Подстановка met-полей: {met.y26.nck}
        import re
        met_pattern = re.compile(r"\{met\.(\w+)\.(\w+)\}")
        for match in met_pattern.finditer(template):
            event_key, field_name = match.group(1), match.group(2)
            event_data = user.get_event_data(event_key)
            value = event_data.get(field_name, "") if event_data else ""
            result = result.replace(match.group(0), str(value))

        return result
