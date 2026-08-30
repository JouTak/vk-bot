from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from vk_api.keyboard import VkKeyboard, VkKeyboardColor

from vkbot.infrastructure.db.event_registry import (
    get_all_events,
    EventDef,
)

# ============================================================
# VK limits / layout constants
# ============================================================

# Формальные лимиты VK.
VK_MAX_KEYBOARD_ROWS = 5
VK_MAX_BUTTONS_PER_ROW = 5
VK_MAX_BUTTON_LABEL_LEN = 40

# Консервативные лимиты для кнопок ивентов.
# 3 кнопки в ряд достаточно для большинства сценариев.
EVENT_MAX_BUTTONS_PER_ROW = 3

# Эвристическая "визуальная ширина" ряда.
# Если кнопки короткие, можно ставить 3 в ряд.
# Если длинные — алгоритм разнесёт их на разные ряды.
#
# Подбирается практически.
# Если в реальной ВК кнопки начнут выглядеть тесно,
# можно уменьшить, например, до 28.0 или 26.0.
EVENT_ROW_WIDTH_LIMIT = 30.0


# ============================================================
# Button model
# ============================================================

@dataclass
class ButtonSpec:
    """Одна кнопка клавиатуры."""

    label: str
    payload: dict[str, Any]
    color: VkKeyboardColor = VkKeyboardColor.PRIMARY


# ============================================================
# Public keyboards
# ============================================================

def build_welcome_keyboard(
        allowed_event_keys: set[str] | None = None,
        page: int = 0,
) -> str:
    """
    Инлайн-клавиатура с кнопками ивентов пользователя.

    Особенности:
    - показывает только разрешённые ивенты;
    - упаковывает кнопки по рядам с учётом длины названий;
    - добавляет пагинацию, если кнопок/рядов слишком много.
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

    buttons: list[ButtonSpec] = []

    for event_def in events:
        label = _get_event_button_label(event_def)
        payload = {
            "type": "event_info",
            "event_key": event_def.key,
        }

        buttons.append(
            ButtonSpec(
                label=label,
                payload=payload,
                color=VkKeyboardColor.PRIMARY,
            )
        )

    rows = _pack_buttons(buttons)

    return _build_paginated_inline_keyboard(rows, page=page)


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
    """
    Обычная неинлайн-клавиатура из списка кнопок.

    Формат кнопки:
    {
        "label": "...",
        "payload": {...},
        "color": "primary",
    }
    """
    keyboard = VkKeyboard(inline=False)

    for btn in buttons:
        color_name = str(btn.get("color", "primary")).upper()
        color = getattr(VkKeyboardColor, color_name, VkKeyboardColor.PRIMARY)

        label = _truncate_label(
            str(btn.get("label", "")),
            VK_MAX_BUTTON_LABEL_LEN,
        )

        keyboard.add_button(
            label=label,
            payload=btn.get("payload", {}),
            color=color,
        )

    return keyboard.get_keyboard()


# ============================================================
# Button packing
# ============================================================

def _pack_buttons(buttons: list[ButtonSpec]) -> list[list[ButtonSpec]]:
    """
    Упаковывает кнопки по рядам.

    Правила:
    - не больше EVENT_MAX_BUTTONS_PER_ROW кнопок в ряду;
    - суммарная визуальная длина кнопок не больше EVENT_ROW_WIDTH_LIMIT;
    - если кнопка длинная, она может стоять отдельно.
    """
    rows: list[list[ButtonSpec]] = []
    current_row: list[ButtonSpec] = []
    current_width = 0.0

    for button in buttons:
        width = _visual_len(button.label)

        if not current_row:
            current_row = [button]
            current_width = width
            continue

        fits_by_count = len(current_row) < EVENT_MAX_BUTTONS_PER_ROW
        fits_by_width = current_width + width <= EVENT_ROW_WIDTH_LIMIT + 1e-6

        if fits_by_count and fits_by_width:
            current_row.append(button)
            current_width += width
        else:
            rows.append(current_row)
            current_row = [button]
            current_width = width

    if current_row:
        rows.append(current_row)

    return rows


# ============================================================
# Pagination
# ============================================================

def _build_paginated_inline_keyboard(
        rows: list[list[ButtonSpec]],
        page: int = 0,
) -> str:
    """
    Собирает инлайн-клавиатуру из рядов кнопок.

    Если рядов не больше VK_MAX_KEYBOARD_ROWS, пагинация не нужна.

    Если рядов больше:
    - один ряд резервируется под навигацию;
    - на странице показывается VK_MAX_KEYBOARD_ROWS - 1 рядов кнопок.
    """
    if not rows:
        return ""

    try:
        page = int(page)
    except (TypeError, ValueError):
        page = 0

    if page < 0:
        page = 0

    if len(rows) <= VK_MAX_KEYBOARD_ROWS:
        page_rows = rows
        pagination_buttons: list[ButtonSpec] = []
    else:
        rows_per_page = VK_MAX_KEYBOARD_ROWS - 1

        page_count = (len(rows) + rows_per_page - 1) // rows_per_page

        if page >= page_count:
            page = page_count - 1

        start = page * rows_per_page
        end = start + rows_per_page
        page_rows = rows[start:end]

        pagination_buttons = _build_pagination_buttons(
            page=page,
            page_count=page_count,
        )

    keyboard = VkKeyboard(inline=True)

    for row_index, row in enumerate(page_rows):
        if row_index > 0:
            keyboard.add_line()

        for button in row:
            keyboard.add_callback_button(
                label=button.label,
                payload=button.payload,
                color=button.color,
            )

    if pagination_buttons:
        if page_rows:
            keyboard.add_line()

        for button in pagination_buttons:
            keyboard.add_callback_button(
                label=button.label,
                payload=button.payload,
                color=button.color,
            )

    return keyboard.get_keyboard()


def _build_pagination_buttons(page: int, page_count: int) -> list[ButtonSpec]:
    """
    Кнопки пагинации.

    Примеры:
        [1/3, →]
        [←, 2/3, →]
        [←, 3/3]
    """
    buttons: list[ButtonSpec] = []

    if page > 0:
        buttons.append(
            ButtonSpec(
                label="←",
                payload={
                    "type": "events_page",
                    "page": page - 1,
                },
                color=VkKeyboardColor.SECONDARY,
            )
        )

    buttons.append(
        ButtonSpec(
            label=f"{page + 1}/{page_count}",
            payload={
                "type": "events_page",
                "page": page,
            },
            color=VkKeyboardColor.SECONDARY,
        )
    )

    if page < page_count - 1:
        buttons.append(
            ButtonSpec(
                label="→",
                payload={
                    "type": "events_page",
                    "page": page + 1,
                },
                color=VkKeyboardColor.SECONDARY,
            )
        )

    return buttons


# ============================================================
# Helpers
# ============================================================

def _get_event_button_label(event_def: EventDef) -> str:
    """
    Возвращает текст кнопки для ивента.

    Приоритет:
    1. button_title
    2. title
    3. key
    """
    label = (
            getattr(event_def, "button_title", None)
            or event_def.title
            or event_def.key
    )

    label = str(label).strip()

    # Схлопываем переводы строк и лишние пробелы.
    label = " ".join(label.split())

    if not label:
        label = event_def.key

    return _truncate_label(label, VK_MAX_BUTTON_LABEL_LEN)


def _truncate_label(label: str, max_len: int) -> str:
    """
    Обрезает подпись кнопки до лимита ВК.
    """
    label = label.strip()

    if len(label) <= max_len:
        return label

    return label[:max_len - 1] + "…"


def _visual_len(text: str) -> float:
    """
    Очень приблизительная оценка визуальной ширины текста.

    Это не пиксели, а эвристика, чтобы не ставить
    три длинные русские надписи в один ряд.

    Правила:
    - кириллица и прочие не-ASCII считаются широкими;
    - ASCII-буквы/цифры считаются чуть уже;
    - пробелы считаются ещё чуть уже.
    """
    total = 0.0

    for ch in text:
        if ch.isspace():
            total += 0.7
        elif ch.isdigit():
            total += 0.7
        elif ch.isascii():
            total += 0.75
        else:
            total += 1.0

    return total
