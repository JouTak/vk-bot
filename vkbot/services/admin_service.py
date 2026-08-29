from __future__ import annotations


from loguru import logger
from sqlalchemy import text
from sqlalchemy.engine import CursorResult

from vkbot.domain.user import User
from vkbot.domain.permissions import PermissionChecker
from vkbot.infrastructure.db.engine import session_scope
from vkbot.infrastructure.db.repositories.user_repo import UserRepository
from vkbot.services.condition_parser import (
    check_and_evaluate,
    validate_condition
)
from vkbot.services.event_service import EventService
from vkbot.services.template_renderer import TemplateRenderer


class AdminService:
    """Все админские команды."""
    DB_QUERY_ROW_COUNT_LIMIT = 50

    def __init__(self, perms: PermissionChecker, vk_client):
        """Сохраняет проверку прав и VK-клиент."""
        self.perms = perms
        self.vk = vk_client

    # ----------------------------------------------------------
    # sender
    # ----------------------------------------------------------

    def sender(self, admin_uid: int, condition: str, message: str) -> str:
        """Выполняет шаблонную рассылку пользователям, подходящим под условие."""
        if not self.perms.is_admin(admin_uid):
            return "Нет доступа"  # ideally unreachable, but double-check

        errors = validate_condition(condition)
        if errors:
            return "Ошибки в условии:\n" + "\n".join(errors)

        template_errors = TemplateRenderer.validate(message)
        if template_errors:
            return "Ошибки в шаблоне:\n" + "\n".join(template_errors)

        compiled = TemplateRenderer.compile(message)

        users = self._load_all_users()
        matched, eval_errors = check_and_evaluate(users, condition)
        if eval_errors:
            return "Ошибки:\n" + "\n".join(eval_errors)

        if not matched:
            return "Совпадений: 0. Никому не отправлено."

        extra_resolver = None
        extra_keys = TemplateRenderer.extra_keys_from_segments(compiled)

        if "fmt.y26_mates" in extra_keys:
            house_map = self._build_y26_house_map(users)
            extra_resolver = self._make_y26_extra_resolver(house_map)
            logger.debug(f"[sender] precomputed y26 houses: {len(house_map)}")

        actions = []
        for user in matched:
            formatted = TemplateRenderer.render(
                compiled,
                user,
                extra_resolver=extra_resolver,
            )
            actions.append({
                "peer_id": user.uid,
                "message": formatted,
            })

        results = self.vk.send_messages(actions)

        sent = 0
        error_texts: list[str] = []

        for r in results:
            if isinstance(r, dict) and r.get("error"):
                error_texts.append(str(r["error"]))
            else:
                sent += 1

        failed = len(actions) - sent

        response = f"Отправлено: {sent}"

        if failed > 0:
            response += f"\nОшибок: {failed}"

        # Уникальные ошибки с сохранением порядка первого появления
        unique_errors = list(dict.fromkeys(error_texts))
        if unique_errors:
            if len(unique_errors) == 1:
                response += f"\nГлавная ошибка:"
            elif 1 < len(unique_errors) <= 20:
                response += f"\nУникальные ошибки ({len(unique_errors)} штук):"
            else:
                response += f"\nУникальные ошибки (первые 20 из {len(unique_errors)}):"
            for err_text in unique_errors[:20]:
                response += f"\n- {err_text}"

        logger.info(f"[sender] condition='{condition}', sent={sent}, failed={failed}")

        return response

    # ----------------------------------------------------------
    # query
    # ----------------------------------------------------------

    def query(self, admin_uid: int, condition: str) -> str:
        """Возвращает список пользователей, подходящих под условие, без отправки сообщений."""
        if not self.perms.is_admin(admin_uid):
            return "Нет доступа"  # ideally unreachable, but double-check

        errors = validate_condition(condition)
        if errors:
            return "Ошибки в условии:\n" + "\n".join(errors)

        users = self._load_all_users()

        matched, eval_errors = check_and_evaluate(users, condition)
        if eval_errors:
            return "Ошибки:\n" + "\n".join(eval_errors)

        if not matched:
            return "Совпадений: 0"

        lines = [
            f"Совпадений: {len(matched)}",
            f"Первые {min(10, len(matched))}:",
        ]

        for user in matched[:10]:
            nck = user.nck or "-"
            fio = user.fio or "-"
            lines.append(f"• {user.isu} | {user.uid} | {nck} | {fio}")

        return "\n".join(lines)

    # ----------------------------------------------------------
    # db
    # ----------------------------------------------------------

    def db_query(self, admin_uid: int, sql: str) -> str:
        """Выполняет сырой SQL-запрос и возвращает результат администратору."""
        if not self.perms.is_admin(admin_uid):
            return "Нет доступа"  # ideally unreachable, but double-check

        if not sql.strip():
            return "Использование: db <SQL запрос>"

        try:
            with session_scope() as s:
                result = s.execute(text(sql))

                if getattr(result, "returns_rows", False):
                    rows = result.fetchall()

                    if not rows:
                        return "Пустой результат"

                    cols = result.keys()
                    header = " | ".join(str(c) for c in cols)

                    lines = [header, "-" * len(header)]

                    for row in rows[:self.DB_QUERY_ROW_COUNT_LIMIT]:
                        lines.append(" | ".join(str(v) for v in row))

                    if len(rows) > self.DB_QUERY_ROW_COUNT_LIMIT:
                        lines.append(f"... и ещё {len(rows) - self.DB_QUERY_ROW_COUNT_LIMIT} строк")

                    output = "\n".join(lines)

                    if len(output) > 4000:
                        output = output[:4000] + "\n... (обрезано)"

                    return output

                else:
                    affected = result.rowcount if isinstance(result, CursorResult) else 0
                    return f"OK. Затронуто строк: {affected}"

        except Exception as e:
            return f"Ошибка SQL: {e}"

    # ----------------------------------------------------------
    # reload
    # ----------------------------------------------------------

    def reload(self, admin_uid: int) -> str:
        """Повторно инъектирует данные всех активных ивентов."""
        if not self.perms.is_admin(admin_uid):
            return "Нет доступа"  # ideally unreachable, but double-check

        event_svc = EventService(user_service=None, vk_client=self.vk)
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

    @staticmethod
    def _load_all_users() -> list[User]:
        """Загружает всех пользователей из БД вместе с данными ивентов."""
        with session_scope() as s:
            return UserRepository(s).list_all_users()

    @staticmethod
    def _build_y26_house_map(users: list[User]) -> dict[str, list[tuple[int, str]]]:
        """
        Предвычисляет карту домиков для y26.

        Формат:
            {
                "1": [(isu, nck), (isu, nck), ...],
                "2": [(isu, nck), ...],
            }

        Используем уже загруженных users, чтобы не делать
        отдельный запрос в БД на каждого пользователя.
        """
        house_map: dict[str, list[tuple[int, str]]] = {}

        for user in users:
            data = user.get_event_data("y26")
            if not data:
                continue

            liv = str(data.get("liv") or "").strip().lower()
            nck = str(data.get("nck") or "").strip()

            if liv in {"", "-", "пока пусто"}:
                continue

            if nck in {"", "-"}:
                continue

            house_map.setdefault(liv, []).append((user.isu, nck))

        for entries in house_map.values():
            entries.sort(key=lambda item: item[1].lower())

        return house_map

    @staticmethod
    def _make_y26_extra_resolver(house_map: dict[str, list[tuple[int, str]]]):
        """
        Возвращает extra_resolver для TemplateRenderer.
        """

        def resolver(key: str, user: User):
            if key != "fmt.y26_mates":
                return None

            data = user.get_event_data("y26") or {}
            liv = str(data.get("liv") or "").strip().lower()

            if liv in {"", "-", "пока пусто"}:
                return False, ""

            entries = house_map.get(liv, [])
            mates = [nck for isu, nck in entries if isu != user.isu]

            return bool(mates), ", ".join(mates)

        return resolver
