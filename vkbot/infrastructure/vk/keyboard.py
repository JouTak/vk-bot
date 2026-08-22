from __future__ import annotations

from vk_api.keyboard import VkKeyboard, VkKeyboardColor


def build_welcome_keyboard(events: list[dict]) -> str:
    """
    Инлайн-клавиатура с кнопками ивентов.
    Каждый элемент: {"key": "y26", "title": "Ягодное 2026"}
    """
    keyboard = VkKeyboard(inline=True)

    for i, event in enumerate(events):
        if i > 0 and i % 3 == 0:
            keyboard.add_line()

        keyboard.add_callback_button(
            label=event["title"][:20],  # VK limit: 20 chars
            payload={"type": "event_info", "event_key": event["key"]},
            color=VkKeyboardColor.PRIMARY,
        )

    return keyboard.get_keyboard()


def build_standard_keyboard(buttons: list[dict]) -> str:
    """
    Обычная (не инлайн) клавиатура.
    Каждый элемент: {"label": "...", "payload": {...}, "color": "positive"}
    """
    keyboard = VkKeyboard(inline=False)
    for btn in buttons:
        color = getattr(VkKeyboardColor, btn.get("color", "primary").upper(), VkKeyboardColor.PRIMARY)
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
