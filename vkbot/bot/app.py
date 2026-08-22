from __future__ import annotations

import time
import traceback

from loguru import logger
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType

from vkbot.config import settings
from vkbot.infrastructure.vk.client import VKClient
from vkbot.infrastructure.vk.keyboard import build_standard_keyboard
from vkbot.infrastructure.db.engine import init_engine, session_scope
from vkbot.infrastructure.db.repositories.user_repo import UserRepository
from vkbot.services.user_service import UserService
from vkbot.services.welcome_service import WelcomeService
from vkbot.domain.permissions import PermissionChecker

SUBSCRIBE_MESSAGE = (
    "Привет! Для получения информации подпишись на группу:\n"
    "https://vk.com/widget_community.php?act=a_subscribe_box&oid=-217494619&state=1|ITMOcraft\n"
    "После подписки отправь ещё одно сообщение."
)


class BotApp:
    def __init__(self):
        init_engine()
        self.vk = VKClient(settings.bot_token, settings.group_id)
        self.longpoll = VkBotLongPoll(self.vk.session, settings.group_id)
        self.perms = PermissionChecker(set(settings.admin_ids))
        self.welcome_svc = WelcomeService()
        logger.info("Bot initialized")

    def run(self):
        logger.info("Starting longpoll loop")
        while True:
            try:
                for event in self.longpoll.listen():
                    self.process_event(event)
            except KeyboardInterrupt:
                logger.info("Shutting down")
                break
            except Exception as e:
                logger.error(f"Loop error: {e}\n{traceback.format_exc()}")
                time.sleep(1)

    def process_event(self, event):
        if event.type == VkBotEventType.MESSAGE_NEW:
            self.handle_message_new(event)
        elif event.type == VkBotEventType.MESSAGE_EVENT:
            self.handle_message_event(event)

    def handle_message_new(self, event):
        uid = event.message.from_id
        msg = (event.message.text or "").strip()

        # 1. Всегда: ensure user exists
        with session_scope() as s:
            repo = UserRepository(s)
            svc = UserService(repo)
            user = svc.ensure_user_exists(uid)

        # 2. Проверка подписки (флудим пока не подпишется)
        if not self.vk.is_member(uid):
            self.vk.send_messages([{"peer_id": uid, "message": SUBSCRIBE_MESSAGE}])
            return

        # 3. АДМИН — всегда отвечаем
        if "админ" in msg.lower():
            self._handle_admin_call(uid, event)
            return

        # 4. Админские команды
        if self.perms.is_admin(uid) and msg:
            response = self._handle_admin_command(uid, msg)
            if response:
                self.vk.send_messages([{"peer_id": uid, "message": response}])
                return

        # 5. Welcome раз в 24 часа
        if self.welcome_svc.should_show_welcome(uid):
            self.welcome_svc.mark_welcome_shown(uid)
            self._send_welcome(uid)
            return

        # 6. Иначе — молчание
        logger.debug(f"Silence: uid={uid}, msg='{msg[:50]}'")

    def handle_message_event(self, event):
        """Обработка нажатий на инлайн-кнопки."""
        payload = event.payload
        if not payload:
            return

        if payload.get("type") == "event_info":
            event_key = payload.get("event_key", "")
            uid = event.user_id
            # TODO: Step 5 — форматирование и отправка инфы по ивенту
            self.vk.send_messages([{
                "peer_id": uid,
                "message": f"[event_info] {event_key} — TODO",
            }])

    def _handle_admin_call(self, uid: int, event):
        """Кнопка / команда АДМИН."""
        first, last = self.vk.get_user_info(uid)
        fio = f"{first} {last}".strip() or f"id{uid}"
        link = f"https://vk.com/gim{self.group_id}?sel={uid}"

        # Юзеру — подтверждение
        keyboard = build_standard_keyboard([
            {"label": "СПАСИБО АДМИН", "payload": {"type": "uncallmanager"}, "color": "negative"},
        ])
        self.vk.send_messages([{
            "peer_id": uid,
            "message": "Принято! Напиши свою проблему следующим сообщением.",
            "keyboard": keyboard,
        }])

        # Админам — уведомление
        admin_msg = f"{fio} вызывает!"
        self.vk.send_messages([
            {"peer_id": admin_uid, "message": f"{admin_msg}\n{link}"}
            for admin_uid in settings.admin_ids
        ])
        logger.info(f"Admin called by uid={uid}")

    def _handle_admin_command(self, uid: int, msg: str) -> str | None:
        """Простейшие админские команды. Полноценная админка — в шаге 6."""
        parts = msg.split()
        if not parts:
            return None

        cmd = parts[0].lower()

        if cmd == "stop":
            logger.info("Bot stopped by admin")
            raise SystemExit(0)

        if cmd == "reload":
            return "[reload] TODO: Step 5 (инъекции)"

        if cmd == "sender":
            return "[sender] TODO: Step 6"

        if cmd == "query":
            return "[query] TODO: Step 6"

        return None

    def _send_welcome(self, uid: int):
        """Приветственное сообщение с кнопками ивентов."""
        # Пока без кнопок ивентов — добавим в шаге 5
        text = (
            "Привет! Мы клуб любителей Майнкрафта ITMOcraft 🎮\n\n"
            "Нажми на кнопку ниже, чтобы узнать актуальную информацию о событиях.\n"
            "Если есть вопросы — напиши АДМИН."
        )
        keyboard = build_standard_keyboard([
            {"label": "ПОЗВАТЬ АДМИНА", "payload": {"type": "callmanager"}, "color": "positive"},
        ])
        self.vk.send_messages([{
            "peer_id": uid,
            "message": text,
            "keyboard": keyboard,
        }])


def main():
    app = BotApp()
    app.run()


if __name__ == "__main__":
    main()
