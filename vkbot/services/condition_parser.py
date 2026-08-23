from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any

from vkbot.domain.user import User
from vkbot.infrastructure.db.event_registry import EVENT_REGISTRY


# ============================================================
# Токены
# ============================================================

class TokenType(Enum):
    FIELD = auto()        # met.y26.bed, isu, uid, fio, grp, nck
    VALUE = auto()        # "hello world", 42, true, unquoted
    OP_COMPARE = auto()   # == != >> >= << <=
    OP_EXIST = auto()     # -> !>
    OP_AND = auto()       # &
    OP_OR = auto()        # |
    LPAREN = auto()       # (
    RPAREN = auto()       # )
    EOF = auto()


@dataclass(frozen=True)
class Token:
    type: TokenType
    value: str
    pos: int  # позиция в строке для ошибок


# ============================================================
# Лексер
# ============================================================

COMPARE_OPS = ("==", "!=", ">>", ">=", "<<", "<=")
EXIST_OPS = ("->", "!>")
BASE_FIELDS = ("isu", "uid", "fio", "grp", "nck")


class LexerError(Exception):
    def __init__(self, message: str, pos: int):
        self.pos = pos
        super().__init__(message)


def tokenize(condition: str) -> list[Token]:
    """
    Разбивает строку условия на токены.
    Поддерживает:
    - Кавычки: "hello world", 'hello world'
    - Экранированные кавычки: "hello \\"world\\""
    - Скобки: ( )
    - Операторы: == != >> >= << <= -> !> & |
    - Поля: met.y26.bed, isu, uid
    - Числа: 42, -1
    - Булевы: true, false
    """
    tokens: list[Token] = []
    i = 0
    n = len(condition)

    while i < n:
        # Пропускаем пробелы
        if condition[i] in (" ", "\t", "\r", "\n"):
            i += 1
            continue

        # Скобки
        if condition[i] == "(":
            tokens.append(Token(TokenType.LPAREN, "(", i))
            i += 1
            continue
        if condition[i] == ")":
            tokens.append(Token(TokenType.RPAREN, ")", i))
            i += 1
            continue

        # Двухсимвольные операторы
        if i + 1 < n:
            two_char = condition[i:i + 2]
            if two_char in COMPARE_OPS:
                tokens.append(Token(TokenType.OP_COMPARE, two_char, i))
                i += 2
                continue
            if two_char in EXIST_OPS:
                tokens.append(Token(TokenType.OP_EXIST, two_char, i))
                i += 2
                continue

        # Логические операторы
        if condition[i] == "&":
            tokens.append(Token(TokenType.OP_AND, "&", i))
            i += 1
            continue
        if condition[i] == "|":
            tokens.append(Token(TokenType.OP_OR, "|", i))
            i += 1
            continue

        # Кавычки (строки с пробелами)
        if condition[i] in ('"', "'"):
            token, i = _read_quoted_string(condition, i)
            tokens.append(token)
            continue

        # Поле или значение (до оператора/пробела/скобки)
        token, i = _read_word(condition, i)
        tokens.append(token)

    tokens.append(Token(TokenType.EOF, "", n))
    return tokens


def _read_quoted_string(condition: str, start: int) -> tuple[Token, int]:
    """Читает строку в кавычках с поддержкой экранирования."""
    quote_char = condition[start]
    i = start + 1
    n = len(condition)
    result: list[str] = []

    while i < n:
        ch = condition[i]

        # Экранирование
        if ch == "\\" and i + 1 < n:
            next_ch = condition[i + 1]
            if next_ch == quote_char:
                result.append(quote_char)
                i += 2
                continue
            elif next_ch == "\\":
                result.append("\\")
                i += 2
                continue
            elif next_ch == "n":
                result.append("\n")
                i += 2
                continue
            elif next_ch == "t":
                result.append("\t")
                i += 2
                continue
            else:
                result.append(ch)
                i += 1
                continue

        # Конец строки
        if ch == quote_char:
            i += 1
            return Token(TokenType.VALUE, "".join(result), start), i

        result.append(ch)
        i += 1

    raise LexerError(f"Незакрытая кавычка {quote_char}", start)


def _read_word(condition: str, start: int) -> tuple[Token, int]:
    """Читает слово (поле или значение) до оператора/пробела/скобки."""
    i = start
    n = len(condition)
    stop_chars = set(" \t\r\n()&|")
    stop_two = COMPARE_OPS + EXIST_OPS

    while i < n:
        if condition[i] in stop_chars:
            break
        if i + 1 < n and condition[i:i + 2] in stop_two:
            break
        i += 1

    raw = condition[start:i]
    if not raw:
        raise LexerError(f"Неожиданный символ: '{condition[start]}'", start)

    # Определяем тип: поле или значение
    if _is_field_path(raw):
        return Token(TokenType.FIELD, raw, start), i
    else:
        return Token(TokenType.VALUE, raw, start), i


def _is_field_path(raw: str) -> bool:
    """Проверяет, является ли токен путём к полю."""
    if raw in BASE_FIELDS:
        return True
    if raw.startswith("met."):
        return True
    return False


# ============================================================
# AST (абстрактное синтаксическое дерево)
# ============================================================

@dataclass
class ASTNode:
    pass


@dataclass
class CompareNode(ASTNode):
    """field op value"""
    field_path: str
    operator: str
    value: Any


@dataclass
class ExistNode(ASTNode):
    """field -> или field !>"""
    field_path: str
    operator: str  # "->" или "!>"


@dataclass
class AndNode(ASTNode):
    left: ASTNode
    right: ASTNode


@dataclass
class OrNode(ASTNode):
    left: ASTNode
    right: ASTNode


@dataclass
class NotNode(ASTNode):
    """Пока не используется, но на будущее."""
    child: ASTNode


# ============================================================
# Парсер (рекурсивный спуск)
# ============================================================

class ParseError(Exception):
    def __init__(self, message: str, pos: int = -1):
        self.pos = pos
        super().__init__(message)


class Parser:
    """
    Грамматика:
        expression  := or_expr
        or_expr     := and_expr ('|' and_expr)*
        and_expr    := primary ('&' primary)*
        primary     := '(' expression ')' | comparison | existence
        comparison  := FIELD compare_op VALUE
        existence   := FIELD exist_op
    """

    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.pos = 0

    def peek(self) -> Token:
        return self.tokens[self.pos]

    def advance(self) -> Token:
        token = self.tokens[self.pos]
        self.pos += 1
        return token

    def expect(self, token_type: TokenType) -> Token:
        token = self.peek()
        if token.type != token_type:
            raise ParseError(
                f"Ожидался {token_type.name}, получен {token.type.name} ('{token.value}')",
                token.pos,
            )
        return self.advance()

    def parse(self) -> ASTNode:
        node = self.parse_or_expr()
        if self.peek().type != TokenType.EOF:
            token = self.peek()
            raise ParseError(
                f"Неожиданный токен: '{token.value}'",
                token.pos,
            )
        return node

    def parse_or_expr(self) -> ASTNode:
        left = self.parse_and_expr()
        while self.peek().type == TokenType.OP_OR:
            self.advance()
            right = self.parse_and_expr()
            left = OrNode(left=left, right=right)
        return left

    def parse_and_expr(self) -> ASTNode:
        left = self.parse_primary()
        while self.peek().type == TokenType.OP_AND:
            self.advance()
            right = self.parse_primary()
            left = AndNode(left=left, right=right)
        return left

    def parse_primary(self) -> ASTNode:
        token = self.peek()

        # Скобки
        if token.type == TokenType.LPAREN:
            self.advance()
            node = self.parse_or_expr()
            self.expect(TokenType.RPAREN)
            return node

        # Поле
        if token.type == TokenType.FIELD:
            field_token = self.advance()
            next_token = self.peek()

            # Оператор существования
            if next_token.type == TokenType.OP_EXIST:
                op_token = self.advance()
                return ExistNode(field_path=field_token.value, operator=op_token.value)

            # Оператор сравнения
            if next_token.type == TokenType.OP_COMPARE:
                op_token = self.advance()
                value_token = self.peek()

                if value_token.type == TokenType.VALUE:
                    self.advance()
                    return CompareNode(
                        field_path=field_token.value,
                        operator=op_token.value,
                        value=value_token.value,
                    )
                elif value_token.type == TokenType.FIELD:
                    # Сравнение двух полей (на будущее)
                    self.advance()
                    return CompareNode(
                        field_path=field_token.value,
                        operator=op_token.value,
                        value=value_token.value,
                    )
                else:
                    raise ParseError(
                        f"Ожидалось значение после '{op_token.value}', получен '{value_token.value}'",
                        value_token.pos,
                    )

            # Просто поле без оператора — ошибка
            raise ParseError(
                f"Ожидался оператор после поля '{field_token.value}'",
                field_token.pos,
            )

        # Значение без поля — ошибка
        if token.type == TokenType.VALUE:
            raise ParseError(
                f"Ожидалось поле, получено значение '{token.value}'",
                token.pos,
            )

        raise ParseError(
            f"Неожиданный токен: '{token.value}'",
            token.pos,
        )


# ============================================================
# Валидация полей
# ============================================================

def validate_field_path(field_path: str) -> list[str]:
    """Проверяет что путь к полю существует в реестре."""
    errors: list[str] = []
    parts = field_path.split(".")

    if parts[0] == "met":
        if len(parts) != 3:
            errors.append(
                f"Неверный формат: '{field_path}'. Ожидается: met.<ивент>.<поле>"
            )
            return errors

        event_key = parts[1]
        field_name = parts[2]

        if event_key not in EVENT_REGISTRY:
            available = ", ".join(sorted(EVENT_REGISTRY.keys()))
            errors.append(f"Неизвестный ивент: '{event_key}'. Доступные: {available}")
            return errors

        event_def = EVENT_REGISTRY[event_key]
        if event_def.get_field(field_name) is None:
            available = ", ".join(event_def.field_names)
            errors.append(
                f"Неизвестное поле '{field_name}' в '{event_key}'. Доступные: {available}"
            )
    elif parts[0] not in BASE_FIELDS:
        available = ", ".join(BASE_FIELDS)
        errors.append(f"Неизвестное поле: '{field_path}'. Доступные: {available}")

    return errors


def validate_condition(condition: str) -> list[str]:
    """
    Полная валидация условия.
    Возвращает список ошибок (пустой = всё ок).
    """
    errors: list[str] = []

    if not condition.strip():
        return ["Условие пустое"]

    # 1. Лексический анализ
    try:
        tokens = tokenize(condition)
    except LexerError as e:
        return [f"Синтаксис (позиция {e.pos}): {e}"]

    # 2. Парсинг
    try:
        parser = Parser(tokens)
        ast = parser.parse()
    except ParseError as e:
        return [f"Парсинг (позиция {e.pos}): {e}"]

    # 3. Валидация полей в AST
    errors.extend(_validate_ast_fields(ast))

    return errors


def _validate_ast_fields(node: ASTNode) -> list[str]:
    """Рекурсивно валидирует все поля в AST."""
    errors: list[str] = []

    if isinstance(node, CompareNode):
        errors.extend(validate_field_path(node.field_path))
    elif isinstance(node, ExistNode):
        errors.extend(validate_field_path(node.field_path))
    elif isinstance(node, AndNode):
        errors.extend(_validate_ast_fields(node.left))
        errors.extend(_validate_ast_fields(node.right))
    elif isinstance(node, OrNode):
        errors.extend(_validate_ast_fields(node.left))
        errors.extend(_validate_ast_fields(node.right))

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


def coerce_value(raw: str, actual_value: Any) -> Any:
    """Приводит строковое значение из условия к типу реального значения."""
    if isinstance(actual_value, bool):
        return raw.lower() in ("1", "true", "yes", "да", "да", "+")
    if isinstance(actual_value, int):
        try:
            return int(raw)
        except ValueError:
            return 0
    return raw


def evaluate_node(user: User, node: ASTNode) -> bool:
    """Вычисляет AST для конкретного юзера."""
    if isinstance(node, OrNode):
        return evaluate_node(user, node.left) or evaluate_node(user, node.right)

    if isinstance(node, AndNode):
        return evaluate_node(user, node.left) and evaluate_node(user, node.right)

    if isinstance(node, ExistNode):
        value = get_field_value(user, node.field_path)
        if node.operator == "->":
            return value is not None
        elif node.operator == "!>":
            return value is None
        return False

    if isinstance(node, CompareNode):
        actual = get_field_value(user, node.field_path)
        if actual is None:
            return False

        # Приводим значение из условия к типу реального значения
        expected = coerce_value(str(node.value), actual)

        try:
            if node.operator == "==":
                return actual == expected
            elif node.operator == "!=":
                return actual != expected
            elif node.operator == ">>":
                return actual > expected
            elif node.operator == ">=":
                return actual >= expected
            elif node.operator == "<<":
                return actual < expected
            elif node.operator == "<=":
                return actual <= expected
        except TypeError:
            return False

    return False


def evaluate_condition(user: User, condition: str) -> bool:
    """
    Публичный API: вычисляет условие для юзера.
    Парсит и вычисляет за один вызов.
    """
    try:
        tokens = tokenize(condition)
        parser = Parser(tokens)
        ast = parser.parse()
        return evaluate_node(user, ast)
    except (LexerError, ParseError):
        return False


# ============================================================
# Публичный API (для sender/query)
# ============================================================

def check_and_evaluate(
    users: list[User], condition: str
) -> tuple[list[User], list[str]]:
    """
    Валидирует условие и фильтрует юзеров.
    Возвращает (совпавшие_юзеры, ошибки_валидации).
    """
    errors = validate_condition(condition)
    if errors:
        return [], errors

    # Парсим один раз, вычисляем много раз
    try:
        tokens = tokenize(condition)
        parser = Parser(tokens)
        ast = parser.parse()
    except (LexerError, ParseError) as e:
        return [], [str(e)]

    matched = []
    for user in users:
        if not user.has_valid_uid:
            continue
        if evaluate_node(user, ast):
            matched.append(user)

    return matched, []