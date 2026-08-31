from __future__ import annotations

import sys
import json
import time
import traceback

from loguru import logger
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType

from vkbot.config import settings
from vkbot.infrastructure.vk.client import VKClient
from vkbot.infrastructure.vk.keyboard import (
    build_welcome_keyboard,
    build_main_menu_keyboard,
)
from vkbot.infrastructure.db.engine import init_engine, session_scope
from vkbot.infrastructure.db.repositories.user_repo import UserRepository
from vkbot.infrastructure.db.repositories.ignored_repo import IgnoredRepository
from vkbot.services.user_service import UserService
from vkbot.services.event_service import EventService
from vkbot.services.message_service import MessageService
from vkbot.services.welcome_service import WelcomeService
from vkbot.services.admin_service import AdminService
from vkbot.domain.permissions import PermissionChecker
from vkbot.cli.migrate import run_migration


class BotApp:
    def __init__(self):
        """Инициализирует БД, VK-клиент, longpoll и сервисы."""
        init_engine()

        self.vk = VKClient(settings.bot_token, settings.group_id)
        self.longpoll = VkBotLongPoll(self.vk.session, settings.group_id)
        self.perms = PermissionChecker(set(settings.admin_ids))

        self.msg_svc = MessageService()
        self.welcome_svc = WelcomeService()
        self.admin_svc = AdminService(
            perms=self.perms,
            vk_client=self.vk,
        )

        logger.info("Bot initialized")

    # ----------------------------------------------------------
    # Главный цикл
    # ----------------------------------------------------------

    def run(self):
        """Запускает инъекцию активных ивентов и основной цикл обработки событий."""
        self._inject_all_events()

        logger.info("Starting longpoll loop")

        while True:
            try:
                for event in self.longpoll.listen():
                    try:
                        self._process_event(event)
                    except SystemExit:
                        raise
                    except Exception as e:
                        logger.error(f"Event error: {e}\n{traceback.format_exc()}")
            except KeyboardInterrupt:
                logger.info("Shutting down")
                break
            except SystemExit:
                raise
            except Exception as e:
                logger.error(f"Loop error: {e}\n{traceback.format_exc()}")

            time.sleep(1)

    # ----------------------------------------------------------
    # Роутинг событий
    # ----------------------------------------------------------

    def _process_event(self, event):
        """Маршрутизирует входящее событие VK в соответствующий обработчик."""
        if event.type == VkBotEventType.MESSAGE_NEW:
            self._handle_message_new(event)
        elif event.type == VkBotEventType.MESSAGE_EVENT:
            self._handle_message_event(event)

    # ----------------------------------------------------------
    # MESSAGE_NEW
    # ----------------------------------------------------------

    def _handle_message_new(self, event):
        """Обрабатывает обычные сообщения: подписку, кнопки, админ-команды и welcome."""
        if getattr(event, "from_chat", False):
            return

        uid = event.message.from_id
        msg = (event.message.text or "").strip()
        ptype = (self._extract_payload(event) or {}).get("type")

        # Гарантируем юзера
        with session_scope() as s:
            UserService(UserRepository(s)).ensure_user_exists(uid)

        # Сначала проверяем подписку
        if not self.vk.is_member(uid):
            self.vk.send_messages([{
                "peer_id": uid,
                "message": self.msg_svc.build_subscribe_message(),
            }])
            return

        # Кнопки/слово АДМИН
        if ptype == "uncallmanager":
            self._toggle_admin_call(uid, force_off=True)
            return

        if ptype == "callmanager" or "админ" in msg.lower():
            self._toggle_admin_call(uid)
            return

        if ptype == "info" or msg.lower() in {"инфо", "info"}:
            if self._send_welcome(uid):
                self.welcome_svc.mark_welcome_shown(uid)
            return

        # Админские команды
        if self.perms.is_admin(uid) and msg:
            response = self._handle_admin_command(uid, msg)
            if response:
                self.vk.send_messages([{"peer_id": uid, "message": response}])
                return

        # Юзер ждёт админа — молчим
        if self._is_ignored(uid):
            logger.debug(f"Ignored silence: uid={uid}")
            return

        # Welcome раз в 24 часа
        if self.welcome_svc.should_show_welcome(uid):
            if self._send_welcome(uid):
                self.welcome_svc.mark_welcome_shown(uid)
            return

        logger.debug(f"Silence: uid={uid}")

    # ----------------------------------------------------------
    # MESSAGE_EVENT
    # ----------------------------------------------------------

    def _handle_message_event(self, event):
        """Обрабатывает нажатия инлайн-кнопок и колбэки VK."""
        obj = event.object if isinstance(event.object, dict) else {}
        payload = obj.get("payload") or {}
        if isinstance(payload, str):
            try:
                payload = json.loads(payload)
            except Exception:
                payload = {}

        uid = int(obj.get("user_id") or obj.get("peer_id") or 0)
        if not uid:
            return

        self._answer_callback(obj)

        with session_scope() as s:
            UserService(UserRepository(s)).ensure_user_exists(uid)

        if not self.vk.is_member(uid):
            self.vk.send_messages([{
                "peer_id": uid,
                "message": self.msg_svc.build_subscribe_message(),
            }])
            return
        ptype = payload.get("type")

        if ptype == "event_info":
            event_key = payload.get("event_key", "")

            with session_scope() as s:
                user = UserRepository(s).get_by_uid(uid)

            if user is None:
                return

            text = self.msg_svc.render_event_info(user, event_key)
            if not text:
                text = f'У тебя пока нет данных по событию "{event_key}".'

            self.vk.send_messages([{"peer_id": uid, "message": text}])

        elif ptype == "callmanager":
            self._toggle_admin_call(uid)

        elif ptype == "uncallmanager":
            self._toggle_admin_call(uid, force_off=True)

        elif ptype == "events_page":
            raw_page = payload.get("page", 0)

            try:
                page = int(raw_page)
            except (TypeError, ValueError):
                page = 0

            with session_scope() as s:
                user = UserRepository(s).get_by_uid(uid)

            if user is None:
                return

            allowed_keys = {
                event_key
                for event_key, event_data in user.met.items()
                if event_data
            }

            events_keyboard = build_welcome_keyboard(allowed_keys, page=page)

            if events_keyboard:
                self.vk.send_messages([{
                    "peer_id": uid,
                    "message": "Твои события:",
                    "keyboard": events_keyboard,
                }])
            else:
                self.vk.send_messages([{
                    "peer_id": uid,
                    "message": "Пока у тебя нет событий с доступными данными.",
                }])

    def _answer_callback(self, obj: dict, text: str = "Данные отправлены"):
        """Отправляет служебный ответ на колбэк инлайн-кнопки."""
        try:
            self.vk.session.method("messages.sendMessageEventAnswer", {
                "event_id": obj.get("event_id"),
                "user_id": obj.get("user_id"),
                "peer_id": obj.get("peer_id"),
                "event_data": json.dumps(
                    {"type": "show_snackbar", "text": text},
                    ensure_ascii=False,
                ),
            })
        except Exception as e:
            logger.error(f"sendMessageEventAnswer failed: {e}")

    # ----------------------------------------------------------
    # Payload из MESSAGE_NEW
    # ----------------------------------------------------------

    @staticmethod
    def _extract_payload(event) -> dict | None:
        """Достаёт и парсит payload из MESSAGE_NEW, если он есть."""
        try:
            raw: str | None = getattr(event.message, "payload", None)
        except Exception:
            try:
                raw = (event.object.get("message") or {}).get("payload")
            except Exception:
                return None

        if isinstance(raw, dict):
            return raw

        try:
            return json.loads(raw)
        except Exception:
            return None

    # ----------------------------------------------------------
    # Вызов админа
    # ----------------------------------------------------------

    @staticmethod
    def _is_ignored(uid: int) -> bool:
        """Проверяет, находится ли пользователь в режиме ожидания админа."""
        with session_scope() as s:
            return IgnoredRepository(s).is_ignored(uid)

    def _toggle_admin_call(self, uid: int, force_off: bool = False):
        """Включает или отключает вызов админа и рассылает уведомления."""
        first, last = self.vk.get_user_info(uid)
        fio = f"{first} {last}".strip() or f"id{uid}"
        link = f"https://vk.com/gim{settings.group_id}?sel={uid}"

        with session_scope() as s:
            repo = IgnoredRepository(s)
            was_calling = repo.is_ignored(uid)
            now_calling = (not was_calling) and not force_off
            if now_calling:
                repo.add(uid)
            elif was_calling:
                repo.remove(uid)

        if now_calling:
            keyboard = build_main_menu_keyboard(admin_called=True)
            self.vk.send_messages([{
                "peer_id": uid,
                "message": "Принято, сейчас позову! Напиши свою проблему следующим сообщением.",
                "keyboard": keyboard,
            }])
            self.vk.send_messages([
                {"peer_id": a, "message": f"{fio} вызывает!\n{link}"}
                for a in settings.admin_ids
            ])
            logger.info(f"Admin called by uid={uid}")
        elif was_calling:
            keyboard = build_main_menu_keyboard(admin_called=False)
            self.vk.send_messages([{
                "peer_id": uid,
                "message": "Надеюсь, вопрос снят!",
                "keyboard": keyboard,
            }])
            self.vk.send_messages([
                {"peer_id": a, "message": f"{fio} больше не вызывает!"}
                for a in settings.admin_ids
            ])
            logger.info(f"Admin call cancelled by uid={uid}")
        else:
            # Сюда попадаем, если вызова не было, а нажали "СПАСИБО АДМИН"
            if force_off:
                self.vk.send_messages([{
                    "peer_id": uid,
                    "message": "Вызов админа уже снят.",
                    "keyboard": build_main_menu_keyboard(admin_called=False),
                }])

    # ----------------------------------------------------------
    # Админские команды
    # ----------------------------------------------------------

    def _handle_admin_command(self, uid: int, msg: str) -> str | None:
        """Разбирает и выполняет админскую команду из ЛС."""
        parts = msg.split()
        if not parts:
            return None

        cmd = parts[0].lower()

        if cmd == "stop":
            logger.info("Bot stopped by admin")
            raise SystemExit(0)

        if cmd == "reload":
            return self.admin_svc.reload(uid)

        if cmd == "sender":
            rest_parts = msg.split(None, 1)

            if len(rest_parts) < 2:
                return "Использование:\nsender <условие>\n<шаблон>"

            rest = rest_parts[1]

            if "\n" not in rest:
                return "Использование:\nsender <условие>\n<шаблон>"

            condition, template = rest.split("\n", 1)

            condition = condition.strip()
            template = template.lstrip("\n")

            if not condition:
                return "Условие не может быть пустым."

            if not template.strip():
                return "Шаблон не может быть пустым."

            return self.admin_svc.sender(uid, condition, template)

        if cmd == "query":
            rest_parts = msg.split(None, 1)

            if len(rest_parts) < 2:
                return "Использование: query <условие>"

            rest = rest_parts[1]
            condition = rest.split("\n", 1)[0].strip()

            if not condition:
                return "Условие не может быть пустым."

            return self.admin_svc.query(uid, condition)

        if cmd == "db":
            sql = msg.removeprefix("db").strip()
            return self.admin_svc.db_query(uid, sql)

        if cmd == "migrate":
            if not settings.enable_migration:
                return "Миграция отключена. Установи ENABLE_MIGRATION=1 и перезапусти бота."

            raw_path = msg.removeprefix("migrate").strip() or "users.txt"
            raw_path = raw_path.replace("\\", "/")

            if raw_path.startswith("./"):
                raw_path = raw_path[2:]

            if raw_path.startswith("/"):
                return "Миграция разрешена только из каталога vkbot/bot/subscribers/"

            if raw_path.startswith("vkbot/bot/subscribers/"):
                raw_path = raw_path[len("vkbot/bot/subscribers/"):]
            elif raw_path.startswith("subscribers/"):
                raw_path = raw_path[len("subscribers/"):]

            base = (settings.base_dir / "vkbot" / "bot" / "subscribers").resolve()
            target = (base / raw_path).resolve()

            if base != target and base not in target.parents:
                return "Миграция разрешена только из каталога vkbot/bot/subscribers/"

            if not target.is_file():
                return f"Файл не найден: {target}"

            try:
                st = run_migration(str(target))
                return (
                    f"Импортировано: {st['imported']}\n"
                    f"Raw (soft issues): {st['raw']}\n"
                    f"Ошибок: {st['errors']}"
                )
            except Exception as e:
                return f"Ошибка миграции: {e}"

        return None

    # ----------------------------------------------------------
    # Welcome
    # ----------------------------------------------------------

    @staticmethod
    def _send_ok(results: list) -> bool:
        """Проверяет, смогло ли отправиться сообщение."""
        return bool(results) and all(
            not (isinstance(r, dict) and r.get("error"))
            for r in results
        )

    def _send_welcome(self, uid: int) -> bool:
        """Отправляет приветственное сообщение и клавиатуру событий; возвращает успех отправки."""
        with session_scope() as s:
            user = UserRepository(s).get_by_uid(uid)
            admin_called = IgnoredRepository(s).is_ignored(uid)

            allowed_keys: set[str] = set()
            if user is not None:
                allowed_keys = {
                    event_key
                    for event_key, event_data in user.met.items()
                    if event_data
                }

        events_keyboard = build_welcome_keyboard(allowed_keys, page=0)
        has_events = bool(events_keyboard)

        text = self.msg_svc.build_welcome_text(has_events=has_events)
        admin_keyboard = build_main_menu_keyboard(admin_called=admin_called)

        main_results = self.vk.send_messages([{
            "peer_id": uid,
            "message": text,
            "keyboard": admin_keyboard,
        }])

        if not self._send_ok(main_results):
            logger.warning(f"Welcome main message failed: uid={uid}")
            return False

        if has_events:
            event_results = self.vk.send_messages([{
                "peer_id": uid,
                "message": "Твои события:",
                "keyboard": events_keyboard,
            }])

            if not self._send_ok(event_results):
                logger.warning(f"Welcome events keyboard failed: uid={uid}")
                # Основной инфо-сообщение уже ушло, поэтому можно не блокировать mark.
                # Если хочешь строго, здесь можно сделать return False.

        return True

    # ----------------------------------------------------------
    # Инъекции
    # ----------------------------------------------------------

    def _inject_all_events(self):
        """Инъектирует данные всех активных ивентов при старте."""
        logger.info("Starting event injection...")

        event_svc = EventService(user_service=None, vk_client=self.vk)
        results = event_svc.inject_all_active()

        for key, stats in results.items():
            logger.info(
                f"  [{key}] source={stats.get('source')}, "
                f"upserted={stats.get('upserted')}, "
                f"skipped={stats.get('skipped')}, "
                f"errors={len(stats.get('errors', []))}"
            )
            for err in stats.get("errors", [])[:5]:
                logger.warning(f"  [{key}] ERROR: {err}")


def setup_logging():
    """Настраивает логирование в консоль и файл."""
    logger.remove()
    logger.add(sys.stderr, level=settings.log_level)
    try:
        logger.add(
            settings.log_path,
            level=settings.log_level,
            rotation="10 MB",
            encoding="utf-8",
        )
    except Exception as e:
        logger.warning(f"Cannot open log file {settings.log_path}: {e}")


def main():
    """Создаёт и запускает приложение бота."""
    setup_logging()
    app = BotApp()
    app.run()


if __name__ == "__main__":
    main()