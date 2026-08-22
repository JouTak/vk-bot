from __future__ import annotations

from typing import Any

from vkbot.infrastructure.db.event_registry import EventDef, FieldDef


def parse_tsv_header(header_line: str) -> dict[str, int]:
    """Парсит заголовок TSV → {название_колонки: индекс}."""
    cols = [c.lower().strip() for c in header_line.strip().split("\t")]
    return {col: idx for idx, col in enumerate(cols)}


def find_column(header_map: dict[str, int], *aliases: str) -> int | None:
    """Ищет колонку по имени или алиасам. Возвращает индекс или None."""
    # Точное совпадение
    for alias in aliases:
        if alias in header_map:
            return header_map[alias]
    # Частичное совпадение
    for alias in aliases:
        for key, idx in header_map.items():
            if alias in key:
                return idx
    return None


def build_column_mapping(event_def: EventDef, header_map: dict[str, int]) -> dict[str, int | None]:
    """
    Строит маппинг: имя_поля → индекс_колонки_в_TSV.
    Использует имя поля как основной алиас.
    """
    mapping = {}
    for field_def in event_def.fields:
        # Пробуем: точное имя поля, потом нижний регистр
        mapping[field_def.name] = find_column(header_map, field_def.name, field_def.name.lower())
    return mapping


def parse_row(
        parts: list[str],
        event_def: EventDef,
        col_mapping: dict[str, int | None],
) -> dict[str, Any]:
    """
    Парсит одну строку TSV в dict по декларации ивента.
    Приводит типы автоматически.
    """
    data: dict[str, Any] = {}

    for field_def in event_def.fields:
        col_idx = col_mapping.get(field_def.name)
        raw = parts[col_idx].strip() if col_idx is not None and col_idx < len(parts) else ""

        data[field_def.name] = coerce_value(raw, field_def)

    return data


def coerce_value(raw: str, field_def: FieldDef) -> Any:
    """Приводит строку из TSV к типу поля."""
    if field_def.type == "int":
        if not raw or raw == "-":
            return field_def.default or 0
        try:
            return int(raw.strip())
        except ValueError:
            return field_def.default or 0

    elif field_def.type == "bool":
        if not raw:
            return field_def.default or False
        return raw.strip().lower() in ("1", "true", "yes", "да", "y", "+")

    elif field_def.type == "str":
        if raw == "-":
            return ""
        return raw

    return raw
