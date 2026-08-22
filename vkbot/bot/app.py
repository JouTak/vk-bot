from __future__ import annotations

import time
import traceback

from loguru import logger
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType

from vkbot.config import settings
from vkbot.infrastructure.vk.client import VKClient
from vkbot.infrastructure.vk.keyboard import (
    build_welcome_keyboard,
    build_standard_keyboard
)
from vkbot.infrastructure.db.engine import init_engine, session_scope
from vkbot.infrastructure.db.repositories.user_repo import UserRepository
from vkbot.services.user_service import UserService
from vkbot.services.event_service import EventService
from vkbot.services.message_service import MessageService
from vkbot.services.welcome_service import WelcomeService
from vkbot.domain.permissions import PermissionChecker


class BotApp:
    def __init__(self):
        init_engine()

        self.vk = VKClient(settings.bot_token, settings.group_id)
        self.longpoll = VkBotLongPoll(self.vk.session, settings.group_id)
        self.perms = PermissionChecker(set(settings.admin_ids))
        self.msg_svc = MessageService()
        self.welcome_svc = WelcomeService()

        logger.info("Bot initialized")

    def run(self):
        # Инъекция при старте
        self._inject_all_events()

        logger.info("Starting longpoll loop")
        while True:
            try:
                for event in self.longpoll.listen():
                    self._process_event(event)
            except KeyboardInterrupt:
                logger.info("Shutting down")
                break
            except Exception as e:
                logger.error(f"Loop error: {e}\n{traceback.format_exc()}")
                time.sleep(1)

    # ----------------------------------------------------------
    # Event routing
    # ----------------------------------------------------------

    def _process_event(self, event):
        if event.type == VkBotEventType.MESSAGE_NEW:
            self._handle_message_new(event)
        elif event.type == VkBotEventType.MESSAGE_EVENT:
            self._handle_message_event(event)

    def _handle_message_new(self, event):
        uid = event.message.from_id
        msg = (event.message.text or "").strip()

        with session_scope() as s:
            repo = UserRepository(s)
            user_svc = UserService(repo)

            # 1. Всегда: ensure user exists
            user = user_svc.ensure_user_exists(uid)

            # 2. Проверка подписки
            if not self.vk.is_member(uid):
                self.vk.send_messages([{
                    "peer_id": uid,
                    "message": self.msg_svc.build_subscribe_message(),
                }])
                return

            # 3. АДМИН
            if "админ" in msg.lower():
                self._handle_admin_call(uid)
                return

            # 4. Админские команды
            if self.perms.is_admin(uid) and msg:
                response = self._handle_admin_command(uid, msg, user_svc)
                if response:
                    self.vk.send_messages([{"peer_id": uid, "message": response}])
                    return

            # 5. Welcome раз в 24 часа
            if self.welcome_svc.should_show_welcome(uid):
                self.welcome_svc.mark_welcome_shown(uid)
                self._send_welcome(uid)
                return

            # 6. Молчание
            logger.debug(f"Silence: uid={uid}")

    def _handle_message_event(self, event):
        """Нажатия на инлайн-кнопки."""
        payload = event.payload
        if not payload:
            return

        if payload.get("type") == "event_info":
            event_key = payload.get("event_key", "")
            uid = event.user_id

            with session_scope() as s:
                repo = UserRepository(s)
                user = repo.get_by_uid(uid)

            if user is None:
                return

            text = self.msg_svc.render_event_info(user, event_key)
            if not text:
                text = f"У тебя пока нет данных по событию «{event_key}»."

            self.vk.send_messages([{"peer_id": uid, "message": text}])

    # ----------------------------------------------------------
    # Handlers
    # ----------------------------------------------------------

    def _handle_admin_call(self, uid: int):
        first, last = self.vk.get_user_info(uid)
        fio = f"{first} {last}".strip() or f"id{uid}"
        link = f"https://vk.com/gim{settings.group_id}?sel={uid}"

        keyboard = build_standard_keyboard([
            {"label": "СПАСИБО АДМИН", "payload": {"type": "uncallmanager"}, "color": "negative"},
        ])
        self.vk.send_messages([{
            "peer_id": uid,
            "message": "Принято! Напиши свою проблему следующим сообщением.",
            "keyboard": keyboard,
        }])

        admin_msg = f"{fio} вызывает!"
        self.vk.send_messages([
            {"peer_id": admin_uid, "message": f"{admin_msg}\n{link}"}
            for admin_uid in settings.admin_ids
        ])
        logger.info(f"Admin called by uid={uid}")

    def _handle_admin_command(self, uid: int, msg: str, user_svc: UserService) -> str | None:
        parts = msg.split()
        if not parts:
            return None

        cmd = parts[0].lower()

        if cmd == "stop":
            logger.info("Bot stopped by admin")
            raise SystemExit(0)

        if cmd == "reload":
            return self._reload_events()

        if cmd == "sender":
            return "[sender] TODO: Step 6"

        if cmd == "query":
            return "[query] TODO: Step 6"

        if cmd == "db":
            return "[db] TODO: Step 6"

        return None

    def _send_welcome(self, uid: int):
        text = self.msg_svc.build_welcome_text()
        keyboard = build_welcome_keyboard()

        # Кнопка АДМИН внизу (обычная, не инлайн)
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
            "keyboard": keyboard,
        }])

    # ----------------------------------------------------------
    # Injection
    # ----------------------------------------------------------

    def _inject_all_events(self):
        logger.info("Starting event injection...")
        with session_scope() as s:
            repo = UserRepository(s)
            user_svc = UserService(repo)
            event_svc = EventService(user_svc, vk_client=self.vk)
            results = event_svc.inject_all_active()

        for key, stats in results.items():
            logger.info(
                f"  [{key}] source={stats.get('source')}, "
                f"upserted={stats.get('upserted')}, "
                f"skipped={stats.get('skipped')}, "
                f"errors={len(stats.get('errors', []))}"
            )

    def _reload_events(self) -> str:
        """Команда reload: повторная инъекция."""
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
        return "\n".join(lines) if lines else "No active events to inject"


def main():
    app = BotApp()
    app.run()


if __name__ == "__main__":
    main()
