from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from vkbot.domain.user import User
from vkbot.services.condition_parser import (
    Parser,
    tokenize,
    ParseError,
    LexerError,
    validate_condition,
    validate_field_path,
    get_field_value,
    coerce_value,
    CompareNode,
    EventExistNode,
    AndNode,
    OrNode,
)

ExtraResolver = Callable[[str, User], tuple[bool, str] | None]


class TemplateSyntaxError(Exception):
    """Ошибка парсинга шаблона."""


# ============================================================
# Узлы шаблона
# ============================================================


@dataclass
class TextNode:
    """
    Обычный текстовый фрагмент шаблона.

    Выводится как есть.
    """

    text: str


@dataclass
class PlaceholderNode:
    """
    Плейсхолдер вида {key}.

    Примеры:
        {nck}
        {met.y26.nck}
        {fmt.y26_mates}
    """

    key: str


@dataclass
class IfNode:
    """
    Условный блок:

        $if (condition)
        $then "..."
        $else "..."
        $end

    Ветка $else может отсутствовать.
    """

    condition: Any
    then_nodes: tuple
    else_nodes: tuple | None


# ============================================================
# TemplateRenderer
# ============================================================


class TemplateRenderer:
    """
    Новый шаблонизатор сообщений.

    Поддерживает:
    - обычный текст;
    - плейсхолдеры {key};
    - условные блоки $if (condition) $then "..." $else "..." $end;
    - вложенные $if;
    - удаление переноса строки через \\ + \\n;
    - экранирование $$ для литерала $.

    Старый синтаксис {слева|справа} больше не поддерживается.
    """

    DIRECTIVE_IF = "$if"
    DIRECTIVE_THEN = "$then"
    DIRECTIVE_ELSE = "$else"
    DIRECTIVE_END = "$end"

    # ----------------------------------------------------------
    # Public API
    # ----------------------------------------------------------

    @classmethod
    def validate(cls, template: str) -> list[str]:
        """
        Проверяет шаблон.

        Возвращает список ошибок.
        Пустой список означает, что шаблон валиден.
        """
        try:
            cls.compile(template)
            return []
        except TemplateSyntaxError as e:
            return [str(e)]

    @classmethod
    def compile(cls, template: str) -> tuple:
        """
        Компилирует шаблон в кортеж узлов.

        Перед парсингом удаляет пары \\ + \\n, чтобы можно было
        переносить служебные директивы без попадания переносов
        строки в итоговый текст.
        """
        prepared = cls._remove_line_continuations(template)
        nodes, pos = cls._parse_template(prepared, 0)

        if pos != len(prepared):
            raise TemplateSyntaxError(
                f"Шаблон распарсился не до конца, позиция {pos}"
            )

        return tuple(nodes)

    @classmethod
    def render_string(
            cls,
            template: str,
            user: User,
            extra_resolver: ExtraResolver | None = None,
    ) -> str:
        """
        Компилирует шаблон и сразу рендерит его для пользователя.
        """
        compiled = cls.compile(template)
        return cls.render(compiled, user, extra_resolver)

    @classmethod
    def render(
            cls,
            compiled: tuple,
            user: User,
            extra_resolver: ExtraResolver | None = None,
    ) -> str:
        """
        Рендерит ранее скомпилированный шаблон для пользователя.
        """
        return "".join(cls._render_nodes(compiled, user, extra_resolver))

    @classmethod
    def used_extra_keys(cls, compiled: tuple) -> set[str]:
        """
        Возвращает множество использованных служебных fmt.* ключей.

        Используется, чтобы заранее понять, нужен ли экстра-резолвер.
        Например, для {fmt.y26_mates}.
        """
        keys: set[str] = set()
        cls._collect_extra_keys(compiled, keys)
        return keys

    @classmethod
    def extra_keys_from_segments(cls, compiled: tuple) -> set[str]:
        """
        Совместимый алиас для used_extra_keys().

        Раньше compiled назывался segments, поэтому оставляем
        это имя, чтобы не ломать вызовы в админском сервисе.
        """
        return cls.used_extra_keys(compiled)

    # ----------------------------------------------------------
    # Preprocessing
    # ----------------------------------------------------------

    @staticmethod
    def _remove_line_continuations(template: str) -> str:
        """
        Удаляет пары \\ + \\n и \\ + \\r\\n.

        Пример:

            Привет \\
            мир

        превратится в:

            Привет мир
        """
        return template.replace("\\\r\n", "").replace("\\\n", "")

    # ----------------------------------------------------------
    # Parsing
    # ----------------------------------------------------------

    @classmethod
    def _parse_template(cls, s: str, start: int) -> tuple[list, int]:
        """
        Парсит шаблон от позиции start до конца строки.

        Возвращает список узлов и позицию остановки.
        """
        nodes: list = []
        i = start
        n = len(s)
        text_start = i

        def flush(end: int):
            nonlocal text_start
            if end > text_start:
                nodes.append(TextNode(s[text_start:end]))
                text_start = end

        while i < n:
            ch = s[i]

            # Экранирование \{ \} \$ вне строк.
            if (
                    ch == "\\"
                    and i + 1 < n
                    and s[i + 1] in "{}$"
            ):
                flush(i)
                nodes.append(TextNode(s[i + 1]))
                i += 2
                text_start = i
                continue

            if ch == "$":
                # $$ -> литерал $
                if s.startswith("$$", i):
                    flush(i)
                    nodes.append(TextNode("$"))
                    i += 2
                    text_start = i
                    continue

                # $if ...
                if cls._match_directive(s, i, cls.DIRECTIVE_IF):
                    flush(i)
                    node, i = cls._parse_if(s, i)
                    nodes.append(node)
                    text_start = i
                    continue

                # Неожиданные $then/$else/$end на верхнем уровне.
                for directive in (
                        cls.DIRECTIVE_THEN,
                        cls.DIRECTIVE_ELSE,
                        cls.DIRECTIVE_END,
                ):
                    if cls._match_directive(s, i, directive):
                        raise TemplateSyntaxError(
                            f"Неожиданный {directive} в позиции {i}"
                        )

                # Неизвестная директива вида $foo.
                if i + 1 < n and (s[i + 1].isalpha() or s[i + 1] == "_"):
                    raise TemplateSyntaxError(
                        f"Неизвестная директива в позиции {i}: "
                        f"{s[i:i + 12]!r}"
                    )

                # Одиночный $ перед цифрами и т.п. считаем обычным текстом.
                i += 1
                continue

            if ch == "{":
                flush(i)
                node, i = cls._parse_placeholder(s, i)
                nodes.append(node)
                text_start = i
                continue

            i += 1

        flush(n)
        return nodes, i

    @classmethod
    def _parse_placeholder(cls, s: str, start: int) -> tuple[PlaceholderNode, int]:
        """
        Парсит плейсхолдер вида {key}.
        """
        assert s[start] == "{"

        end = s.find("}", start + 1)
        if end == -1:
            raise TemplateSyntaxError(
                f"Незакрытый плейсхолдер в позиции {start}"
            )

        key = s[start + 1:end].strip()
        if not key:
            raise TemplateSyntaxError(
                f"Пустой плейсхолдер в позиции {start}"
            )

        errors = validate_field_path(key)
        if errors:
            raise TemplateSyntaxError(
                f"Ошибка плейсхолдера {{{key}}}: " + "; ".join(errors)
            )

        return PlaceholderNode(key=key), end + 1

    @classmethod
    def _parse_if(cls, s: str, start: int) -> tuple[IfNode, int]:
        """
        Парсит конструкцию:

            $if (condition)
            $then "..."
            $else "..."
            $end
        """
        i = start

        if not cls._match_directive(s, i, cls.DIRECTIVE_IF):
            raise TemplateSyntaxError(f"Ожидался $if в позиции {i}")

        i += len(cls.DIRECTIVE_IF)
        i = cls._skip_spaces(s, i)

        condition, i = cls._parse_condition(s, i)

        i = cls._skip_spaces(s, i)

        if not cls._match_directive(s, i, cls.DIRECTIVE_THEN):
            raise TemplateSyntaxError(
                f"Ожидался $then после условия в позиции {i}"
            )

        i += len(cls.DIRECTIVE_THEN)
        i = cls._skip_spaces(s, i)

        then_nodes, i = cls._parse_branch(s, i)

        i = cls._skip_spaces(s, i)

        else_nodes = None

        if cls._match_directive(s, i, cls.DIRECTIVE_ELSE):
            i += len(cls.DIRECTIVE_ELSE)
            i = cls._skip_spaces(s, i)

            else_nodes, i = cls._parse_branch(s, i)
            i = cls._skip_spaces(s, i)

        if not cls._match_directive(s, i, cls.DIRECTIVE_END):
            raise TemplateSyntaxError(
                f"Ожидался $end в позиции {i}"
            )

        i += len(cls.DIRECTIVE_END)

        return IfNode(
            condition=condition,
            then_nodes=tuple(then_nodes),
            else_nodes=tuple(else_nodes) if else_nodes is not None else None,
        ), i

    @classmethod
    def _parse_branch(cls, s: str, start: int) -> tuple[list, int]:
        """
        Парсит ветку $then/$else.

        Ветка обязательно должна быть строкой в кавычках:

            "..."
            '...'

        Содержимое ветки рекурсивно парсится как шаблон.
        """
        i = start

        if i >= len(s):
            raise TemplateSyntaxError(
                f"Ожидалась строка в кавычках в позиции {i}"
            )

        quote = s[i]
        if quote not in ("'", '"'):
            raise TemplateSyntaxError(
                f"Ветка $then/$else должна быть строкой в кавычках, "
                f"позиция {i}"
            )

        i += 1
        n = len(s)
        buf: list[str] = []

        while i < n:
            ch = s[i]

            if ch == "\\":
                if i + 1 >= n:
                    raise TemplateSyntaxError(
                        f"Обрыв экранирования в позиции {i}"
                    )

                nxt = s[i + 1]

                if nxt == quote:
                    buf.append(quote)
                    i += 2
                    continue

                if nxt == "\\":
                    buf.append("\\")
                    i += 2
                    continue

                if nxt == "n":
                    buf.append("\n")
                    i += 2
                    continue

                if nxt == "t":
                    buf.append("\t")
                    i += 2
                    continue

                if nxt == "r":
                    buf.append("\r")
                    i += 2
                    continue

                # Неизвестный escape: оставляем сам символ после \.
                buf.append(nxt)
                i += 2
                continue

            if ch == quote:
                i += 1
                break

            buf.append(ch)
            i += 1
        else:
            raise TemplateSyntaxError(
                f"Незакрытая строка ветки, начиная с позиции {start}"
            )

        inner = "".join(buf)

        nodes, pos = cls._parse_template(inner, 0)
        if pos != len(inner):
            raise TemplateSyntaxError(
                "Внутренний шаблон ветки распарсился не до конца"
            )

        return nodes, i

    @classmethod
    def _parse_condition(cls, s: str, start: int) -> tuple[Any, int]:
        """
        Парсит условие в скобках после $if.

        Пример:

            $if (met.y26.chk == 1 & met.y26.bed == 1)

        Возвращает AST условия и позицию после закрывающей скобки.
        """
        i = start

        if i >= len(s) or s[i] != "(":
            raise TemplateSyntaxError(
                f"Ожидалась '(' после $if в позиции {i}"
            )

        depth = 1
        j = i + 1
        n = len(s)
        in_quote: str | None = None
        escaped = False

        while j < n:
            ch = s[j]

            if escaped:
                escaped = False
                j += 1
                continue

            if ch == "\\":
                escaped = True
                j += 1
                continue

            if in_quote:
                if ch == in_quote:
                    in_quote = None
                j += 1
                continue

            if ch in ("'", '"'):
                in_quote = ch
                j += 1
                continue

            if ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
                if depth == 0:
                    break

            j += 1

        if j >= n or depth != 0:
            raise TemplateSyntaxError(
                f"Незакрытая скобка условия, позиция {i}"
            )

        condition_text = s[i + 1:j]

        errors = validate_condition(condition_text)
        if errors:
            raise TemplateSyntaxError(
                "Ошибка условия: " + "; ".join(errors)
            )

        try:
            ast = Parser(tokenize(condition_text)).parse()
        except (LexerError, ParseError) as e:
            raise TemplateSyntaxError(f"Ошибка парсинга условия: {e}") from e

        return ast, j + 1

    # ----------------------------------------------------------
    # Rendering
    # ----------------------------------------------------------

    @classmethod
    def _render_nodes(
            cls,
            nodes: tuple,
            user: User,
            extra_resolver: ExtraResolver | None,
    ) -> list[str]:
        """
        Рендерит список узлов шаблона.
        """
        out: list[str] = []

        for node in nodes:
            if isinstance(node, TextNode):
                out.append(node.text)

            elif isinstance(node, PlaceholderNode):
                resolved = cls._resolve_placeholder(
                    user,
                    node.key,
                    extra_resolver,
                )

                if resolved is None:
                    # После валидации сюда попасть не должно.
                    continue

                ok, value = resolved
                out.append(value if ok else "")

            elif isinstance(node, IfNode):
                if cls._evaluate_condition(node.condition, user, extra_resolver):
                    out.extend(
                        cls._render_nodes(node.then_nodes, user, extra_resolver)
                    )
                elif node.else_nodes is not None:
                    out.extend(
                        cls._render_nodes(node.else_nodes, user, extra_resolver)
                    )

        return out

    @classmethod
    def _evaluate_condition(
            cls,
            node: Any,
            user: User,
            extra_resolver: ExtraResolver | None,
    ) -> bool:
        """
        Вычисляет условие.

        Обычные поля вычисляются через condition_parser.
        Служебные поля вида fmt.* вычисляются через extra_resolver.
        """
        if isinstance(node, OrNode):
            return (
                    cls._evaluate_condition(node.left, user, extra_resolver)
                    or cls._evaluate_condition(node.right, user, extra_resolver)
            )

        if isinstance(node, AndNode):
            return (
                    cls._evaluate_condition(node.left, user, extra_resolver)
                    and cls._evaluate_condition(node.right, user, extra_resolver)
            )

        if isinstance(node, EventExistNode):
            has_event = user.has_event(node.event_key)

            if node.operator == "->":
                return has_event

            if node.operator == "!>":
                return not has_event

            return False

        if isinstance(node, CompareNode):
            if node.field_path.startswith("fmt."):
                resolved = cls._resolve_placeholder(
                    user,
                    node.field_path,
                    extra_resolver,
                )

                if resolved is None:
                    return False

                exists, value = resolved
                actual: Any = value if exists else ""
            else:
                actual = get_field_value(user, node.field_path)

                if actual is None:
                    return False

            try:
                expected = coerce_value(str(node.value), actual)

                if node.operator == "==":
                    return actual == expected
                if node.operator == "!=":
                    return actual != expected
                if node.operator == ">>":
                    return actual > expected
                if node.operator == ">=":
                    return actual >= expected
                if node.operator == "<<":
                    return actual < expected
                if node.operator == "<=":
                    return actual <= expected

            except (TypeError, ValueError):
                return False

        return False

    @staticmethod
    def _resolve_placeholder(
            user: User,
            key: str,
            extra_resolver: ExtraResolver | None,
    ):
        """
        Возвращает (exists, value) для плейсхолдера.

        Если ключ неизвестен, возвращает None.
        Если ключ известен, но значения нет, возвращает (False, "").
        """
        key = key.strip()

        # Служебные вычисляемые плейсхолдеры.
        # Например, {fmt.y26_mates}.
        if key.startswith("fmt."):
            if extra_resolver is not None:
                resolved = extra_resolver(key, user)
                if resolved is not None:
                    return resolved

            return False, ""

        if key == "isu":
            return user.has_real_isu, str(user.isu)

        if key == "uid":
            return user.has_valid_uid, str(user.uid)

        if key in ("fio", "grp", "nck"):
            v = (getattr(user, key, "") or "").strip()
            return (bool(v) and v != "-"), v

        if key.startswith("met."):
            parts = key.split(".")

            if len(parts) == 3:
                data = user.get_event_data(parts[1])
                raw = data.get(parts[2]) if data else None

                if raw is None:
                    return False, ""

                if isinstance(raw, bool):
                    return True, ("Да" if raw else "Нет")

                s = str(raw).strip()
                return (bool(s) and s != "-"), s

            return False, ""

        return None

    # ----------------------------------------------------------
    # Extra keys collection
    # ----------------------------------------------------------

    @classmethod
    def _collect_extra_keys(cls, nodes: tuple, keys: set[str]) -> None:
        """
        Рекурсивно собирает все использованные служебные fmt.* ключи.
        """
        for node in nodes:
            if isinstance(node, PlaceholderNode):
                if node.key.startswith("fmt."):
                    keys.add(node.key)

            elif isinstance(node, IfNode):
                cls._collect_condition_extra_keys(node.condition, keys)

                if node.then_nodes:
                    cls._collect_extra_keys(node.then_nodes, keys)

                if node.else_nodes:
                    cls._collect_extra_keys(node.else_nodes, keys)

    @classmethod
    def _collect_condition_extra_keys(cls, node: Any, keys: set[str]) -> None:
        """
        Собирает служебные ключи из условий.
        """
        if isinstance(node, CompareNode):
            if node.field_path.startswith("fmt."):
                keys.add(node.field_path)

        elif isinstance(node, AndNode):
            cls._collect_condition_extra_keys(node.left, keys)
            cls._collect_condition_extra_keys(node.right, keys)

        elif isinstance(node, OrNode):
            cls._collect_condition_extra_keys(node.left, keys)
            cls._collect_condition_extra_keys(node.right, keys)

    # ----------------------------------------------------------
    # Helpers
    # ----------------------------------------------------------

    @staticmethod
    def _skip_spaces(s: str, i: int) -> int:
        """
        Пропускает пробелы, табы и переводы строк.

        Используется между служебными словами $if/$then/$else/$end.
        """
        n = len(s)

        while i < n and s[i] in (" ", "\t", "\r", "\n"):
            i += 1

        return i

    @staticmethod
    def _is_ascii_word_char(ch: str) -> bool:
        return ch.isascii() and (ch.isalnum() or ch == "_")

    @staticmethod
    def _match_directive(s: str, i: int, directive: str) -> bool:
        """
        Проверяет, что в позиции i находится директива.

        Директива не должна сливаться с ASCII-словом:
            $endif   -> не $end
            $end123  -> не $end
            $end_foo -> не $end

        Но кириллица и другие не-ASCII символы считаются обычным текстом:
            $endБерёшь -> $end + "Берёшь"
        """
        if not s.startswith(directive, i):
            return False

        pos = i + len(directive)

        if pos >= len(s):
            return True

        nxt = s[pos]

        return not TemplateRenderer._is_ascii_word_char(nxt)
