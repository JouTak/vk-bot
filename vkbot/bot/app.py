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
    build_standard_keyboard,
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


class BotApp:
    def __init__(self):
        init_engine()

        self.vk = VKClient(settings.bot_token, settings.group_id)
        self.longpoll = VkBotLongPoll(self.vk.session, settings.group_id)
        self.perms = PermissionChecker(set(settings.admin_ids))
        self.msg_svc = MessageService()
        self.welcome_svc = WelcomeService()
        self.admin_svc = AdminService(
            perms=self.perms,
            vk_client=self.vk
        )
        logger.info("Bot initialized")

    # ----------------------------------------------------------
    # Главный цикл
    # ----------------------------------------------------------

    def run(self):
        # Инъекция при старте
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
        if event.type == VkBotEventType.MESSAGE_NEW:
            self._handle_message_new(event)
        elif event.type == VkBotEventType.MESSAGE_EVENT:
            self._handle_message_event(event)

    # ----------------------------------------------------------
    # MESSAGE_NEW: обычные сообщения и НЕ-инлайн кнопки
    # ----------------------------------------------------------

    def _handle_message_new(self, event):
        if getattr(event, "from_chat", False):
            return  # чаты игнорируем

        uid = event.message.from_id
        msg = (event.message.text or "").strip()
        ptype = (self._extract_payload(event) or {}).get("type")

        # 1. Всегда: юзер в базе
        with session_scope() as s:
            UserService(UserRepository(s)).ensure_user_exists(uid)

        # 2. Подписка (флудим, пока не подпишется)
        if not self.vk.is_member(uid):
            self.vk.send_messages([{
                "peer_id": uid,
                "message": self.msg_svc.build_subscribe_message(),
            }])
            return

        # 3. Кнопки/слово АДМИН (toggle)
        if ptype == "uncallmanager":
            self._toggle_admin_call(uid, force_off=True)
            return
        if ptype == "callmanager" or "админ" in msg.lower():
            self._toggle_admin_call(uid)
            return

        # 4. Админские команды
        if self.perms.is_admin(uid) and msg:
            response = self._handle_admin_command(uid, msg)
            if response:
                self.vk.send_messages([{"peer_id": uid, "message": response}])
                return

        # 5. Юзер в режиме «ждёт админа» → молчание
        if self._is_ignored(uid):
            logger.debug(f"Ignored silence: uid={uid}")
            return

        # 6. Welcome раз в 24 часа
        if self.welcome_svc.should_show_welcome(uid):
            self.welcome_svc.mark_welcome_shown(uid)
            self._send_welcome(uid)
            return

        # 7. Молчание
        logger.debug(f"Silence: uid={uid}")

    # ----------------------------------------------------------
    # MESSAGE_EVENT: инлайн-кнопки (payload в event.object)
    # ----------------------------------------------------------

    def _handle_message_event(self, event):
        obj = event.object if isinstance(event.object, dict) else {}
        payload = obj.get("payload") or {}
        uid = int(obj.get("user_id") or obj.get("peer_id") or 0)
        if not uid:
            return

        # 1. ПЕРВЫМ ДЕЛОМ квитуем кнопку — снимаем крутилку
        self._answer_callback(obj)

        # 2. Кнопка = контакт: юзер должен попасть в базу
        with session_scope() as s:
            UserService(UserRepository(s)).ensure_user_exists(uid)

        ptype = payload.get("type")

        if ptype == "event_info":
            event_key = payload.get("event_key", "")
            with session_scope() as s:
                user = UserRepository(s).get_by_uid(uid)
            if user is None:
                return
            text = self.msg_svc.render_event_info(user, event_key)
            if not text:
                text = f"У тебя пока нет данных по событию «{event_key}»."
            self.vk.send_messages([{"peer_id": uid, "message": text}])

        elif ptype == "callmanager":
            self._toggle_admin_call(uid)

        elif ptype == "uncallmanager":
            self._toggle_admin_call(uid, force_off=True)

    def _answer_callback(self, obj: dict, text: str = "Данные отправлены"):
        """Квитирование нажатия callback-кнопки. Без этого кнопка крутится вечно."""
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
    # Payload из MESSAGE_NEW (нажатие НЕ-инлайн кнопки)
    # ----------------------------------------------------------

    @staticmethod
    def _extract_payload(event) -> dict | None:
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
    # Вызов админа: toggle + ignored-список
    # ----------------------------------------------------------

    def _is_ignored(self, uid: int) -> bool:
        with session_scope() as s:
            return IgnoredRepository(s).is_ignored(uid)

    def _toggle_admin_call(self, uid: int, force_off: bool = False):
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
            keyboard = build_standard_keyboard([
                {"label": "СПАСИБО АДМИН", "payload": {"type": "uncallmanager"}, "color": "negative"},
            ])
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
        else:
            keyboard = build_standard_keyboard([
                {"label": "ПОЗВАТЬ АДМИНА", "payload": {"type": "callmanager"}, "color": "positive"},
            ])
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

    # ----------------------------------------------------------
    # Админские команды
    # ----------------------------------------------------------

    def _handle_admin_command(self, uid: int, msg: str) -> str | None:
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
            if len(parts) < 3:
                return "Использование: sender <условие> <сообщение>"
            condition = parts[1]
            message = msg.split(None, 2)[2]  # всё после условия
            return self.admin_svc.sender(uid, condition, message)

        if cmd == "query":
            if len(parts) < 2:
                return "Использование: query <условие>"
            condition = parts[1]
            return self.admin_svc.query(uid, condition)

        if cmd == "db":
            sql = msg.removeprefix("db").strip()
            return self.admin_svc.db_query(uid, sql)

        if cmd == "migrate":
            if not settings.enable_migration:
                return "Миграция отключена. Установи ENABLE_MIGRATION=1 и перезапусти бота."
            from vkbot.cli.migrate import run_migration
            path = msg.removeprefix("migrate").strip() or "subscribers/users.txt"
            try:
                st = run_migration(path)
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

    def _send_welcome(self, uid: int):
        text = self.msg_svc.build_welcome_text()

        # Обычная кнопка АДМИН внизу
        admin_keyboard = build_standard_keyboard([
            {"label": "ПОЗВАТЬ АДМИНА", "payload": {"type": "callmanager"}, "color": "positive"},
        ])
        self.vk.send_messages([{
            "peer_id": uid,
            "message": text,
            "keyboard": admin_keyboard,
        }])

        # Инлайн-кнопки ивентов отдельным сообщением
        self.vk.send_messages([{
            "peer_id": uid,
            "message": "Актуальные события:",
            "keyboard": build_welcome_keyboard(),
        }])

    # ----------------------------------------------------------
    # Инъекции
    # ----------------------------------------------------------

    def _inject_all_events(self):
        logger.info("Starting event injection...")
        with session_scope() as s:
            user_svc = UserService(UserRepository(s))
            event_svc = EventService(user_svc, vk_client=self.vk)
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
    setup_logging()
    app = BotApp()
    app.run()


if __name__ == "__main__":
    main()
