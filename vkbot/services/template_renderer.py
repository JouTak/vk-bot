from __future__ import annotations
import re
from typing import Callable
from vkbot.domain.user import User
from vkbot.services.condition_parser import (
    Parser,
    tokenize,
    evaluate_node,
    ParseError,
    LexerError,
    validate_field_path,
    validate_condition,
)

ExtraResolver = Callable[[str, User], tuple[bool, str] | None]


class TemplateRenderer:
    """
    Общий шаблонизатор сообщений.
    Используется:
    - в админском sender;
    - в пользовательских информационных сообщениях ивентов.
    Поддерживает:
    - плейсхолдеры: {isu}, {nck}, {met.y26.bed}
    - привязки по ключу: {met.y26.nmb|Твой телефон: {met.y26.nmb}}
    - привязки по условию: {met.e26.plc>>0|Твоё место: {met.e26.plc}}
    - служебные вычисляемые ключи: {fmt.y26_mates}
    """
    KEY_RE = re.compile(r"^[\w.]+$", re.ASCII)
    PLACEHOLDER_RE = re.compile(r"\{([^{}|]+)\}")
    EXTRA_KEY_PREFIX = "fmt."
    KNOWN_EXTRA_KEYS = {
        "fmt.y26_mates",
    }

    # ----------------------------------------------------------
    # Public API
    # ----------------------------------------------------------
    @classmethod
    def validate(cls, template: str) -> list[str]:
        errors: list[str] = []
        for seg in cls.compile(template):
            kind = seg[0]
            if kind == "ph":
                key = seg[1].strip()
                if not cls._is_known_extra_key(key) and validate_field_path(key):
                    errors.append(f"Неизвестный ключ '{{{key}}}'")
            elif kind == "bind":
                _, bkind, payload, right, raw, left = seg
                if bkind == "key":
                    if not cls._is_known_extra_key(payload) and validate_field_path(payload):
                        errors.append(f"Неизвестный ключ '{{{raw}}}'")
                elif bkind == "cond":
                    cond_errors = validate_condition(left)
                    if cond_errors:
                        errors.append(
                            f"Ошибка условия в '{{{raw}}}': "
                            + "; ".join(cond_errors)
                        )
                elif bkind == "error":
                    errors.append(f"Не могу разобрать '{{{raw}}}': {payload}")
                errors.extend(cls._validate_placeholders_in_text(right))
        return errors

    @classmethod
    def render_string(
            cls,
            template: str,
            user: User,
            extra_resolver: ExtraResolver | None = None,
    ) -> str:
        compiled = cls.compile(template)
        return cls.render(compiled, user, extra_resolver)

    @classmethod
    def render(
            cls,
            segments,
            user: User,
            extra_resolver: ExtraResolver | None = None,
    ) -> str:
        out: list[str] = []
        for seg in segments:
            kind = seg[0]
            if kind == "text":
                out.append(seg[1])
            elif kind == "ph":
                resolved = cls._resolve_placeholder(
                    user,
                    seg[1].strip(),
                    extra_resolver,
                )
                if resolved is None:
                    out.append("{" + seg[1] + "}")
                else:
                    ok, value = resolved
                    out.append(value if ok else "")
            else:  # bind
                _, bkind, payload, right, raw, _left = seg
                if bkind == "key":
                    resolved = cls._resolve_placeholder(
                        user,
                        payload,
                        extra_resolver,
                    )
                    if resolved is None or not resolved[0]:
                        continue
                    if "{" in right:
                        out.append(cls._render_placeholders(right, user, extra_resolver))
                    else:
                        out.append(right + resolved[1])
                elif bkind == "cond":
                    if evaluate_node(user, payload):
                        out.append(cls._render_placeholders(right, user, extra_resolver))
                else:  # error
                    out.append("{" + raw + "}")
        return "".join(out)

    # ----------------------------------------------------------
    # Compile
    # ----------------------------------------------------------
    @classmethod
    def compile(cls, template: str) -> tuple:
        """
        Разбивает шаблон на сегменты.
        Типы сегментов:
        - ("text", текст)
        - ("ph", ключ)
        - ("bind", "key", ключ, правая_часть, исходный_контент, левая_часть)
        - ("bind", "cond", AST, правая_часть, исходный_контент, левая_часть)
        - ("bind", "error", текст_ошибки, правая_часть, исходный_контент, левая_часть)
        """
        segments: list = []
        i = 0
        n = len(template)
        while i < n:
            start = template.find("{", i)
            if start == -1:
                segments.append(("text", template[i:]))
                break
            if start > i:
                segments.append(("text", template[i:start]))
            depth = 0
            j = start
            while j < n:
                if template[j] == "{":
                    depth += 1
                elif template[j] == "}":
                    depth -= 1
                    if depth == 0:
                        break
                j += 1
            if j >= n:
                segments.append(("text", template[start:]))
                break
            content = template[start + 1:j]
            left, has_sep, right = cls._split_left_right(content)
            left_s = left.strip()
            if not has_sep:
                segments.append(("ph", content))
            else:
                if cls.KEY_RE.fullmatch(left_s):
                    segments.append(("bind", "key", left_s, right, content, left_s))
                else:
                    try:
                        ast = Parser(tokenize(left_s)).parse()
                        segments.append(("bind", "cond", ast, right, content, left_s))
                    except (LexerError, ParseError) as e:
                        segments.append(("bind", "error", str(e), right, content, left_s))
            i = j + 1
        return tuple(segments)

    @classmethod
    def used_extra_keys(cls, template: str) -> set[str]:
        return cls.extra_keys_from_segments(cls.compile(template))

    @classmethod
    def extra_keys_from_segments(cls, segments) -> set[str]:
        keys: set[str] = set()

        for seg in segments:
            kind = seg[0]

            if kind == "ph":
                key = seg[1].strip()
                if key.startswith(cls.EXTRA_KEY_PREFIX):
                    keys.add(key)

            elif kind == "bind":
                _, bkind, payload, right, _raw, _left = seg

                if bkind == "key" and payload.startswith(cls.EXTRA_KEY_PREFIX):
                    keys.add(payload)

                for match in cls.PLACEHOLDER_RE.finditer(right):
                    key = match.group(1).strip()
                    if key.startswith(cls.EXTRA_KEY_PREFIX):
                        keys.add(key)

        return keys

    # ----------------------------------------------------------
    # Validation helpers
    # ----------------------------------------------------------
    @classmethod
    def _validate_placeholders_in_text(cls, text: str) -> list[str]:
        errors: list[str] = []
        for match in cls.PLACEHOLDER_RE.finditer(text):
            key = match.group(1).strip()
            if not cls._is_known_extra_key(key) and validate_field_path(key):
                errors.append(f"Неизвестный ключ внутри привязки '{{{key}}}'")
        return errors

    @classmethod
    def _is_known_extra_key(cls, key: str) -> bool:
        return key in cls.KNOWN_EXTRA_KEYS

    # ----------------------------------------------------------
    # Render helpers
    # ----------------------------------------------------------
    @staticmethod
    def _split_left_right(content: str) -> tuple[str, bool, str]:
        """
        Первая '|' на нулевой глубине скобок — разделитель.
        """
        depth = 0
        for idx, ch in enumerate(content):
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth = max(0, depth - 1)
            elif ch == "|" and depth == 0:
                return content[:idx], True, content[idx + 1:]
        return content, False, ""

    @classmethod
    def _render_placeholders(
            cls,
            text: str,
            user: User,
            extra_resolver: ExtraResolver | None = None,
    ) -> str:
        def repl(m: re.Match) -> str:
            resolved = cls._resolve_placeholder(
                user,
                m.group(1).strip(),
                extra_resolver,
            )
            if resolved is None:
                return m.group(0)
            ok, value = resolved
            return value if ok else ""

        return cls.PLACEHOLDER_RE.sub(repl, text)

    @staticmethod
    def _resolve_placeholder(
            user: User,
            key: str,
            extra_resolver: ExtraResolver | None = None,
    ):
        """
        Возвращает (exists, value) или None, если ключ неизвестен.
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
