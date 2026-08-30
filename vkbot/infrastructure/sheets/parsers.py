from __future__ import annotations

from typing import Any

from vkbot.infrastructure.db.event_registry import EventDef, FieldDef


def parse_tsv_header(header_line: str) -> dict[str, int]:
    """Парсит заголовок TSV → {название_колонки: индекс}."""
    cols = [c.lower().strip() for c in header_line.strip().split("\t")]
    return {col: idx for idx, col in enumerate(cols)}


def find_column(header_map: dict[str, int], *aliases: str) -> int | None:
    """Ищет колонку по имени или алиасам. Возвращает индекс или None."""
    for alias in aliases:
        alias_l = str(alias).lower()
        if alias_l in header_map:
            return header_map[alias_l]

    for alias in aliases:
        alias_l = str(alias).lower()
        for key, idx in header_map.items():
            if alias_l in key:
                return idx

    return None


def find_column_verbose(header_map: dict[str, int], *aliases: str) -> tuple[int | None, str]:
    """
    Ищет колонку и возвращает:
    - (idx, "exact")
    - (idx, "partial")
    - (None, "ambiguous: col1, col2")
    - (None, "not_found")
    """
    for alias in aliases:
        alias_l = str(alias).lower()
        if alias_l in header_map:
            return header_map[alias_l], "exact"

    for alias in aliases:
        alias_l = str(alias).lower()
        matches = [(key, idx) for key, idx in header_map.items() if alias_l in key]

        if len(matches) == 1:
            return matches[0][1], "partial"

        if len(matches) > 1:
            names = ", ".join(sorted(key for key, _ in matches))
            return None, f"ambiguous: {names}"

    return None, "not_found"


def build_column_mapping(event_def: EventDef, header_map: dict[str, int]) -> dict[str, int | None]:
    """Старый совместимый маппинг."""
    mapping = {}
    for field_def in event_def.fields:
        mapping[field_def.name] = find_column(
            header_map,
            field_def.name,
            field_def.name.lower(),
        )

    return mapping


def build_column_mapping_verbose(
    event_def: EventDef,
    header_map: dict[str, int],
) -> tuple[dict[str, int | None], list[str]]:
    """
    Строит маппинг полей и возвращает список предупрежений.
    """
    mapping: dict[str, int | None] = {}
    warnings: list[str] = []
    idx_to_col = {idx: col for col, idx in header_map.items()}

    for field_def in event_def.fields:
        idx, how = find_column_verbose(
            header_map,
            field_def.name,
            field_def.name.lower(),
        )

        mapping[field_def.name] = idx

        if idx is None:
            warnings.append(f"Поле '{field_def.name}' не найдено ({how})")
        elif how != "exact":
            col_name = idx_to_col.get(idx, "?")
            warnings.append(
                f"Поле '{field_def.name}' сопоставлено с '{col_name}' ({how})"
            )

    return mapping, warnings


def parse_row(
    parts: list[str],
    event_def: EventDef,
    col_mapping: dict[str, int | None],
) -> dict[str, Any]:
    """Парсит одну строку TSV в dict по декларации ивента."""
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