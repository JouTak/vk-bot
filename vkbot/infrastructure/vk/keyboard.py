from __future__ import annotations

from vk_api.keyboard import VkKeyboard, VkKeyboardColor

from vkbot.infrastructure.db.event_registry import get_all_events


def build_welcome_keyboard(allowed_event_keys: set[str] | None = None) -> str:
    """
    Инлайн-клавиатура с кнопками ивентов.

    Если allowed_event_keys передан, показываются только разрешённые ивенты.
    Если разрешённых ивентов нет, возвращается пустая строка.
    """
    events = get_all_events()

    if allowed_event_keys is not None:
        events = [
            event_def
            for event_def in events
            if event_def.key in allowed_event_keys
        ]

    if not events:
        return ""

    keyboard = VkKeyboard(inline=True)

    for i, event_def in enumerate(events):
        if i > 0 and i % 3 == 0:
            keyboard.add_line()

        keyboard.add_callback_button(
            label=event_def.title[:40],  # VK limit: 40 chars
            payload={"type": "event_info", "event_key": event_def.key},
            color=VkKeyboardColor.PRIMARY,
        )

    return keyboard.get_keyboard()


def build_main_menu_keyboard(admin_called: bool = False) -> str:
    """
    Обычная неинлайн-клавиатура:
    - ПОЗВАТЬ АДМИНА / СПАСИБО АДМИН
    - ИНФО
    """
    keyboard = VkKeyboard(inline=False)

    if admin_called:
        keyboard.add_button(
            label="СПАСИБО АДМИН",
            payload={"type": "uncallmanager"},
            color=VkKeyboardColor.NEGATIVE,
        )
    else:
        keyboard.add_button(
            label="ПОЗВАТЬ АДМИНА",
            payload={"type": "callmanager"},
            color=VkKeyboardColor.POSITIVE,
        )

    keyboard.add_line()

    keyboard.add_button(
        label="ИНФО",
        payload={"type": "info"},
        color=VkKeyboardColor.PRIMARY,
    )

    return keyboard.get_keyboard()


def build_standard_keyboard(buttons: list[dict]) -> str:
    """Обычная (не инлайн) клавиатура."""
    keyboard = VkKeyboard(inline=False)

    for btn in buttons:
        color = getattr(
            VkKeyboardColor,
            btn.get("color", "primary").upper(),
            VkKeyboardColor.PRIMARY,
        )

        keyboard.add_button(
            label=btn["label"],
            payload=btn.get("payload", {}),
            color=color,
        )

    return keyboard.get_keyboard()
