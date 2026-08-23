from __future__ import annotations

from vk_api.keyboard import VkKeyboard, VkKeyboardColor

from vkbot.infrastructure.db.event_registry import get_all_events


def build_welcome_keyboard() -> str:
    """
    Инлайн-клавиатура с кнопками ВСЕХ ивентов.
    active=False влияет только на инъекции (старт/reload),
    но не на видимость кнопок.
    """
    events = get_all_events()
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


def build_link_keyboard(buttons: list[dict]) -> str:
    """Инлайн-клавиатура с кнопками-ссылками."""
    keyboard = VkKeyboard(inline=True)
    for btn in buttons:
        keyboard.add_openlink_button(
            label=btn["label"],
            payload=btn.get("payload", {}),
            link=btn["link"],
        )
    return keyboard.get_keyboard()
