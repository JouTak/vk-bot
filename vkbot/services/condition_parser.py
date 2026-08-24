from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import Any

from vkbot.domain.user import User
from vkbot.infrastructure.db.event_registry import EVENT_REGISTRY


# ============================================================
# Токены
# ============================================================


class TokenType(Enum):
    FIELD = auto()
    VALUE = auto()
    OP_COMPARE = auto()
    OP_EXIST = auto()
    OP_AND = auto()
    OP_OR = auto()
    LPAREN = auto()
    RPAREN = auto()
    EOF = auto()


@dataclass(frozen=True)
class Token:
    type: TokenType
    value: str
    pos: int


# ============================================================
# Лексер
# ============================================================


COMPARE_OPS = ("==", "!=", ">>", ">=", "<<", "<=")
EXIST_OPS = ("->", "!>")
BASE_FIELDS = ("isu", "uid", "fio", "grp", "nck")

BOOL_ACCEPTED_VALUES = {
    "0",
    "1",
    "true",
    "false",
    "yes",
    "no",
    "да",
    "нет",
    "+",
    "-",
}


class LexerError(Exception):
    def __init__(self, message: str, pos: int):
        self.pos = pos
        super().__init__(message)


def tokenize(condition: str) -> list[Token]:
    tokens: list[Token] = []
    i = 0
    n = len(condition)

    while i < n:
        if condition[i] in (" ", "\t", "\r", "\n"):
            i += 1
            continue

        if condition[i] == "(":
            tokens.append(Token(TokenType.LPAREN, "(", i))
            i += 1
            continue

        if condition[i] == ")":
            tokens.append(Token(TokenType.RPAREN, ")", i))
            i += 1
            continue

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

        if condition[i] == "&":
            tokens.append(Token(TokenType.OP_AND, "&", i))
            i += 1
            continue

        if condition[i] == "|":
            tokens.append(Token(TokenType.OP_OR, "|", i))
            i += 1
            continue

        if condition[i] in ('"', "'"):
            token, i = _read_quoted_string(condition, i)
            tokens.append(token)
            continue

        token, i = _read_word(condition, i)
        tokens.append(token)

    tokens.append(Token(TokenType.EOF, "", n))
    return tokens


def _read_quoted_string(condition: str, start: int) -> tuple[Token, int]:
    quote_char = condition[start]
    i = start + 1
    n = len(condition)
    result: list[str] = []

    while i < n:
        ch = condition[i]

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

        if ch == quote_char:
            i += 1
            return Token(TokenType.VALUE, "".join(result), start), i

        result.append(ch)
        i += 1

    raise LexerError(f"Незакрытая кавычка {quote_char}", start)


def _read_word(condition: str, start: int) -> tuple[Token, int]:
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

    if _is_field_path(raw):
        return Token(TokenType.FIELD, raw, start), i

    return Token(TokenType.VALUE, raw, start), i


def _is_field_path(raw: str) -> bool:
    if raw in BASE_FIELDS:
        return True

    if raw.startswith("met."):
        return True

    return False


# ============================================================
# AST
# ============================================================


@dataclass
class ASTNode:
    pass


@dataclass
class CompareNode(ASTNode):
    field_path: str
    operator: str
    value: Any


@dataclass
class EventExistNode(ASTNode):
    event_key: str
    operator: str


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
    child: ASTNode


# ============================================================
# Парсер
# ============================================================


class ParseError(Exception):
    def __init__(self, message: str, pos: int = -1):
        self.pos = pos
        super().__init__(message)


class Parser:
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

        if token.type == TokenType.LPAREN:
            self.advance()
            node = self.parse_or_expr()
            self.expect(TokenType.RPAREN)
            return node

        if token.type == TokenType.FIELD:
            field_token = self.advance()
            next_token = self.peek()

            # Новый синтаксис существования ивента:
            # y26->met
            # y26!>met
            if next_token.type == TokenType.OP_EXIST:
                op_token = self.advance()
                target_token = self.peek()

                if (
                    target_token.type != TokenType.VALUE
                    or str(target_token.value).strip().lower() != "met"
                ):
                    raise ParseError(
                        "Ожидалось 'met' после оператора существования",
                        target_token.pos,
                    )

                self.advance()

                return EventExistNode(
                    event_key=str(field_token.value).strip().lower(),
                    operator=op_token.value,
                )

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

                raise ParseError(
                    f"Ожидалось значение после '{op_token.value}', получен '{value_token.value}'",
                    value_token.pos,
                )

            raise ParseError(
                f"Ожидался оператор после поля '{field_token.value}'",
                field_token.pos,
            )

        if token.type == TokenType.VALUE:
            value_token = self.advance()
            next_token = self.peek()

            # Сюда попадают ключи ивентов, например:
            # y26->met
            # s25!>met
            if next_token.type == TokenType.OP_EXIST:
                op_token = self.advance()
                target_token = self.peek()

                if (
                    target_token.type != TokenType.VALUE
                    or str(target_token.value).strip().lower() != "met"
                ):
                    raise ParseError(
                        "Ожидалось 'met' после оператора существования",
                        target_token.pos,
                    )

                self.advance()

                return EventExistNode(
                    event_key=str(value_token.value).strip().lower(),
                    operator=op_token.value,
                )

            raise ParseError(
                f"Ожидалось поле, получено значение '{value_token.value}'",
                value_token.pos,
            )

        raise ParseError(
            f"Неожиданный токен: '{token.value}'",
            token.pos,
        )


# ============================================================
# Валидация полей и типов
# ============================================================


def validate_field_path(field_path: str) -> list[str]:
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


def get_field_type(field_path: str) -> str | None:
    parts = field_path.split(".")

    if parts[0] == "met":
        if len(parts) != 3:
            return None

        event_key = parts[1]
        field_name = parts[2]

        event_def = EVENT_REGISTRY.get(event_key)
        if event_def is None:
            return None

        field_def = event_def.get_field(field_name)
        if field_def is None:
            return None

        return field_def.type

    if field_path in ("isu", "uid"):
        return "int"

    if field_path in ("fio", "grp", "nck"):
        return "str"

    return None


def validate_value_type(raw: str, field_type: str) -> str | None:
    raw = str(raw).strip()

    if field_type == "int":
        try:
            int(raw)
        except ValueError:
            return f"Значение '{raw}' должно быть целым числом."

    elif field_type == "bool":
        if raw.lower() not in BOOL_ACCEPTED_VALUES:
            return (
                f"Значение '{raw}' должно быть булевым: "
                "1/0, true/false, yes/no, да/нет."
            )

    return None


def validate_condition(condition: str) -> list[str]:
    errors: list[str] = []

    if not condition.strip():
        return ["Условие пустое"]

    try:
        tokens = tokenize(condition)
    except LexerError as e:
        return [f"Синтаксис (позиция {e.pos}): {e}"]

    try:
        parser = Parser(tokens)
        ast = parser.parse()
    except ParseError as e:
        return [f"Парсинг (позиция {e.pos}): {e}"]

    errors.extend(_validate_ast_fields(ast))

    return errors


def _validate_ast_fields(node: ASTNode) -> list[str]:
    errors: list[str] = []

    if isinstance(node, CompareNode):
        field_errors = validate_field_path(node.field_path)
        errors.extend(field_errors)

        if not field_errors:
            if isinstance(node.value, str):
                field_type = get_field_type(node.field_path)

                if field_type is not None:
                    type_error = validate_value_type(node.value, field_type)
                    if type_error:
                        errors.append(type_error)
            else:
                errors.append("Сравнение поля с полем пока не поддерживается.")

    elif isinstance(node, EventExistNode):
        if node.event_key not in EVENT_REGISTRY:
            available = ", ".join(sorted(EVENT_REGISTRY.keys()))
            errors.append(
                f"Неизвестный ивент: '{node.event_key}'. Доступные: {available}"
            )

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
    if isinstance(actual_value, bool):
        return str(raw).strip().lower() in ("1", "true", "yes", "да", "+")

    if isinstance(actual_value, int):
        try:
            return int(str(raw).strip())
        except ValueError as e:
            raise ValueError(f"Не удалось привести '{raw}' к числу") from e

    return raw


def evaluate_node(user: User, node: ASTNode) -> bool:
    if isinstance(node, OrNode):
        return evaluate_node(user, node.left) or evaluate_node(user, node.right)

    if isinstance(node, AndNode):
        return evaluate_node(user, node.left) and evaluate_node(user, node.right)

    if isinstance(node, EventExistNode):
        has_event = user.has_event(node.event_key)

        if node.operator == "->":
            return has_event

        if node.operator == "!>":
            return not has_event

        return False

    if isinstance(node, CompareNode):
        actual = get_field_value(user, node.field_path)

        if actual is None:
            return False

        try:
            expected = coerce_value(str(node.value), actual)

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

        except (TypeError, ValueError):
            return False

    return False


def evaluate_condition(user: User, condition: str) -> bool:
    try:
        tokens = tokenize(condition)
        parser = Parser(tokens)
        ast = parser.parse()
        return evaluate_node(user, ast)
    except (LexerError, ParseError):
        return False


# ============================================================
# Публичный API
# ============================================================


def check_and_evaluate(
    users: list[User],
    condition: str,
) -> tuple[list[User], list[str]]:
    errors = validate_condition(condition)

    if errors:
        return [], errors

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