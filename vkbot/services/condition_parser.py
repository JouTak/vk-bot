from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from vkbot.domain.user import User
from vkbot.infrastructure.db.event_registry import EVENT_REGISTRY

# ============================================================
# Лексер: разбивает строку условия на токены
# ============================================================

# Приоритет операторов (от низшего к высшему)
OPERATORS_LOGIC = ("|", "&")
OPERATORS_EXIST = ("->", "!>")
OPERATORS_COMPARE = ("==", "!=", ">>", ">=", "<<", "<=")

# Валидные поля для условий
BASE_FIELDS = ("isu", "uid", "fio", "grp", "nck")


@dataclass(frozen=True)
class Token:
    type: str  # "field", "operator", "value", "logic"
    value: str


def tokenize(condition: str) -> list[Token]:
    """Разбивает условие на токены."""
    tokens: list[Token] = []
    i = 0
    s = condition.strip()

    while i < len(s):
        # Пропускаем пробелы
        if s[i] == " ":
            i += 1
            continue

        # Логические операторы
        if s[i] == "|":
            tokens.append(Token("logic", "|"))
            i += 1
            continue
        if s[i] == "&":
            tokens.append(Token("logic", "&"))
            i += 1
            continue

        # Операторы существования (двухсимвольные)
        if s[i:i + 2] in OPERATORS_EXIST:
            tokens.append(Token("operator", s[i:i + 2]))
            i += 2
            continue

        # Операторы сравнения (двухсимвольные)
        if s[i:i + 2] in OPERATORS_COMPARE:
            tokens.append(Token("operator", s[i:i + 2]))
            i += 2
            continue

        # Поле или значение (до следующего оператора)
        # Ищем конец токена: до оператора или логического символа
        j = i
        while j < len(s) and s[j] not in " |&" and s[j:j + 2] not in OPERATORS_EXIST and s[
                                                                                         j:j + 2] not in OPERATORS_COMPARE:
            j += 1
            # Односимвольные операторы
            if j < len(s) and s[j] in "|&":
                break

        raw = s[i:j].strip()
        if raw:
            # Определяем тип: поле (содержит '.') или значение
            if "." in raw or raw in BASE_FIELDS:
                tokens.append(Token("field", raw))
            else:
                tokens.append(Token("value", raw))
        i = j

    return tokens


# ============================================================
# Валидация
# ============================================================

def validate_condition(condition: str) -> list[str]:
    """
    Проверяет синтаксис условия.
    Возвращает список ошибок (пустой = всё ок).
    """
    errors: list[str] = []

    if not condition.strip():
        return ["Условие пустое"]

    tokens = tokenize(condition)
    if not tokens:
        return ["Не удалось разобрать условие"]

    # Проверяем каждый токен-поле
    for token in tokens:
        if token.type == "field":
            field_path = token.value
            parts = field_path.split(".")

            if parts[0] == "met":
                if len(parts) != 3:
                    errors.append(f"Неверный формат поля: '{field_path}'. Ожидается: met.<ивент>.<поле>")
                    continue
                event_key = parts[1]
                field_name = parts[2]
                if event_key not in EVENT_REGISTRY:
                    errors.append(f"Неизвестный ивент: '{event_key}'. Доступные: {', '.join(EVENT_REGISTRY.keys())}")
                    continue
                event_def = EVENT_REGISTRY[event_key]
                if event_def.get_field(field_name) is None:
                    available = ", ".join(event_def.field_names)
                    errors.append(f"Неизвестное поле '{field_name}' в ивенте '{event_key}'. Доступные: {available}")
            elif parts[0] not in BASE_FIELDS:
                errors.append(f"Неизвестное поле: '{field_path}'. Доступные: {', '.join(BASE_FIELDS)}")

    # Проверяем структуру: не должно быть двух операторов подряд
    for i in range(len(tokens) - 1):
        if tokens[i].type == "operator" and tokens[i + 1].type == "operator":
            errors.append(f"Два оператора подряд: '{tokens[i].value}' '{tokens[i + 1].value}'")

    return errors


# ============================================================
# Вычисление
# ============================================================

def get_field_value(user: User, field_path: str) -> Any:
    """Достаёт значение поля из юзера по пути."""
    parts = field_path.split(".")

    if parts[0] == "met":
        if len(parts) != 3:
            return None
        event_key, field_name = parts[1], parts[2]
        event_data = user.get_event_data(event_key)
        if not event_data:
            return None
        return event_data.get(field_name)

    # Базовые поля
    if parts[0] == "isu":
        return user.isu
    if parts[0] == "uid":
        return user.uid
    if parts[0] == "fio":
        return user.fio
    if parts[0] == "grp":
        return user.grp
    if parts[0] == "nck":
        return user.nck

    return None


def coerce_value(raw: str, target_type: str) -> Any:
    """Приводит строковое значение из условия к нужному типу."""
    if target_type == "int":
        try:
            return int(raw)
        except ValueError:
            return 0
    elif target_type == "bool":
        return raw.lower() in ("1", "true", "yes", "да", "да", "2")
    return raw


def evaluate_condition(user: User, condition: str) -> bool:
    """Вычисляет условие для конкретного юзера."""
    # Обработка логических операторов (рекурсивно)
    if "|" in condition:
        return any(evaluate_condition(user, part) for part in condition.split("|"))
    if "&" in condition:
        return all(evaluate_condition(user, part) for part in condition.split("&"))

    # Операторы существования
    if "->" in condition:
        field_path = condition.split("->")[0].strip()
        value = get_field_value(user, field_path)
        return value is not None
    if "!>" in condition:
        field_path = condition.split("!>")[0].strip()
        value = get_field_value(user, field_path)
        return value is None

    # Операторы сравнения
    for op in OPERATORS_COMPARE:
        if op in condition:
            parts = condition.split(op, 1)
            if len(parts) != 2:
                return False

            field_path = parts[0].strip()
            raw_value = parts[1].strip()

            actual = get_field_value(user, field_path)
            if actual is None:
                return False

            # Определяем тип для приведения
            expected = _coerce_by_operator(op, raw_value)

            # Сравнение
            try:
                if op == "==":
                    return actual == expected
                elif op == "!=":
                    return actual != expected
                elif op == ">>":
                    return actual > expected
                elif op == ">=":
                    return actual >= expected
                elif op == "<<":
                    return actual < expected
                elif op == "<=":
                    return actual <= expected
            except TypeError:
                return False

    return False


def _coerce_by_operator(op: str, raw: str) -> Any:
    """Приводит значение в зависимости от контекста."""
    # Пытаемся как int
    if raw.lstrip("-").isdigit():
        return int(raw)
    # Bool
    if raw.lower() in ("true", "false", "да", "нет"):
        return raw.lower() in ("true", "да", "1")
    return raw


# ============================================================
# Публичный API
# ============================================================

def check_and_evaluate(users: list[User], condition: str) -> tuple[list[User], list[str]]:
    """
    Валидирует условие и фильтрует юзеров.
    Возвращает (совпавшие_юзеры, ошибки_валидации).
    """
    errors = validate_condition(condition)
    if errors:
        return [], errors

    matched = []
    for user in users:
        # Пропускаем юзеров без валидного uid
        if not user.has_valid_uid:
            continue
        if evaluate_condition(user, condition):
            matched.append(user)

    return matched, []
