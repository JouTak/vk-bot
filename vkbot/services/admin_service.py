from __future__ import annotations

import re

from loguru import logger
from sqlalchemy import text
from sqlalchemy.engine import CursorResult

from vkbot.domain.user import User
from vkbot.domain.permissions import PermissionChecker
from vkbot.infrastructure.db.engine import session_scope
from vkbot.infrastructure.db.repositories.user_repo import UserRepository
from vkbot.services.condition_parser import (
    check_and_evaluate,
    validate_condition,
    validate_field_path,
    tokenize,
    Parser,
    evaluate_node,
    ParseError,
    LexerError,
)
from vkbot.services.event_service import EventService


class AdminService:
    """Все админские команды."""
    DB_QUERY_ROW_COUNT_LIMIT = 50

    def __init__(self, perms: PermissionChecker, vk_client):
        self.perms = perms
        self.vk = vk_client

    # ----------------------------------------------------------
    # sender
    # ----------------------------------------------------------

    def sender(self, admin_uid: int, condition: str, message: str) -> str:
        if not self.perms.is_admin(admin_uid):
            return "Нет доступа"  # ideally unreachable, but double-check

        errors = validate_condition(condition)
        if errors:
            return "Ошибки в условии:\n" + "\n".join(errors)

        template_errors = self._validate_template(message)
        if template_errors:
            return "Ошибки в шаблоне:\n" + "\n".join(template_errors)

        compiled = self._compile_template(message)

        users = self._load_all_users()
        matched, eval_errors = check_and_evaluate(users, condition)
        if eval_errors:
            return "Ошибки:\n" + "\n".join(eval_errors)

        if not matched:
            return "Совпадений: 0. Никому не отправлено."

        actions = []
        for user in matched:
            formatted = self._render_template(compiled, user)
            actions.append({
                "peer_id": user.uid,
                "message": formatted,
            })

        results = self.vk.send_messages(actions)

        sent = 0
        error_texts: list[str] = []

        for r in results:
            if isinstance(r, dict) and r.get("error"):
                error_texts.append(str(r["error"]))
            else:
                sent += 1

        failed = len(actions) - sent

        response = f"Отправлено: {sent}"

        if failed > 0:
            response += f"\nОшибок: {failed}"

        # Уникальные ошибки с сохранением порядка первого появления
        unique_errors = list(dict.fromkeys(error_texts))
        if unique_errors:
            if len(unique_errors) == 1:
                response += f"\nГлавная ошибка:"
            elif 1 < len(unique_errors) <= 20:
                response += f"\nУникальные ошибки ({len(unique_errors)} штук):"
            else:
                response += f"\nУникальные ошибки (первые 20 из {len(unique_errors)}):"
            for err_text in unique_errors[:20]:
                response += f"\n- {err_text}"

        logger.info(f"[sender] condition='{condition}', sent={sent}, failed={failed}")

        return response

    # ----------------------------------------------------------
    # query
    # ----------------------------------------------------------

    def query(self, admin_uid: int, condition: str) -> str:
        if not self.perms.is_admin(admin_uid):
            return "Нет доступа"  # ideally unreachable, but double-check

        errors = validate_condition(condition)
        if errors:
            return "Ошибки в условии:\n" + "\n".join(errors)

        users = self._load_all_users()

        matched, eval_errors = check_and_evaluate(users, condition)
        if eval_errors:
            return "Ошибки:\n" + "\n".join(eval_errors)

        if not matched:
            return "Совпадений: 0"

        lines = [
            f"Совпадений: {len(matched)}",
            f"Первые {min(10, len(matched))}:",
        ]

        for user in matched[:10]:
            nck = user.nck or "-"
            fio = user.fio or "-"
            lines.append(f"• {user.isu} | {user.uid} | {nck} | {fio}")

        return "\n".join(lines)

    # ----------------------------------------------------------
    # db
    # ----------------------------------------------------------

    def db_query(self, admin_uid: int, sql: str) -> str:
        if not self.perms.is_admin(admin_uid):
            return "Нет доступа"  # ideally unreachable, but double-check

        if not sql.strip():
            return "Использование: db <SQL запрос>"

        try:
            with session_scope() as s:
                result = s.execute(text(sql))

                if getattr(result, "returns_rows", False):
                    rows = result.fetchall()

                    if not rows:
                        return "Пустой результат"

                    cols = result.keys()
                    header = " | ".join(str(c) for c in cols)

                    lines = [header, "-" * len(header)]

                    for row in rows[:self.DB_QUERY_ROW_COUNT_LIMIT]:
                        lines.append(" | ".join(str(v) for v in row))

                    if len(rows) > self.DB_QUERY_ROW_COUNT_LIMIT:
                        lines.append(f"... и ещё {len(rows) - self.DB_QUERY_ROW_COUNT_LIMIT} строк")

                    output = "\n".join(lines)

                    if len(output) > 4000:
                        output = output[:4000] + "\n... (обрезано)"

                    return output

                else:
                    affected = result.rowcount if isinstance(result, CursorResult) else 0
                    return f"OK. Затронуто строк: {affected}"

        except Exception as e:
            return f"Ошибка SQL: {e}"

    # ----------------------------------------------------------
    # reload
    # ----------------------------------------------------------

    def reload(self, admin_uid: int) -> str:
        if not self.perms.is_admin(admin_uid):
            return "Нет доступа"  # ideally unreachable, but double-check

        event_svc = EventService(user_service=None, vk_client=self.vk)
        results = event_svc.inject_all_active()

        lines = []

        for key, stats in results.items():
            lines.append(
                f"{key}: source={stats.get('source')}, "
                f"upserted={stats.get('upserted')}, "
                f"skipped={stats.get('skipped')}"
            )

        return "\n".join(lines) if lines else "Нет активных ивентов для инъекции"

    # ----------------------------------------------------------
    # Хелперы
    # ----------------------------------------------------------

    @staticmethod
    def _load_all_users() -> list[User]:
        with session_scope() as s:
            return UserRepository(s).list_all_users()

    # ----------------------------------------------------------
    # Шаблоны sender: {ключ|текст} и {условие|текст}
    # ----------------------------------------------------------

    _KEY_RE = re.compile(r"^[\w.]+$", re.ASCII)

    @classmethod
    def _validate_template(cls, template: str) -> list[str]:
        errors: list[str] = []
        for seg in cls._compile_template(template):
            kind = seg[0]

            if kind == "ph":
                if validate_field_path(seg[1].strip()):
                    errors.append(f"Неизвестный ключ '{{{seg[1]}}}'")

            elif kind == "bind":
                _, bkind, payload, _right, raw = seg
                if bkind == "key":
                    if validate_field_path(payload):
                        errors.append(f"Неизвестный ключ '{{{raw}}}'")
                elif bkind == "error":
                    errors.append(f"Не могу разобрать '{{{raw}}}': {payload}")

        return errors

    @classmethod
    def _compile_template(cls, template: str) -> list:
        """Разбивает шаблон на сегменты: текст / плейсхолдер / привязка."""
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

            # ищем парную закрывающую скобку с учётом вложенности
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

            if j >= n:  # незакрытая скобка — остальное как текст
                segments.append(("text", template[start:]))
                break

            content = template[start + 1:j]
            left, has_sep, right = cls._split_left_right(content)

            if not has_sep:
                segments.append(("ph", content))
            else:
                left_s = left.strip()
                if cls._KEY_RE.fullmatch(left_s):
                    segments.append(("bind", "key", left_s, right, content))
                else:
                    try:
                        ast = Parser(tokenize(left_s)).parse()
                        segments.append(("bind", "cond", ast, right, content))
                    except (LexerError, ParseError) as e:
                        segments.append(("bind", "error", str(e), right, content))

            i = j + 1

        return segments

    @staticmethod
    def _split_left_right(content: str) -> tuple[str, bool, str]:
        """Первая '|' на нулевой глубине скобок — разделитель."""
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
    def _render_template(cls, segments: list, user: User) -> str:
        out: list[str] = []

        for seg in segments:
            kind = seg[0]

            if kind == "text":
                out.append(seg[1])

            elif kind == "ph":
                resolved = cls._resolve_placeholder(user, seg[1].strip())
                if resolved is None:
                    out.append("{" + seg[1] + "}")  # неизвестный ключ — как есть
                else:
                    ok, value = resolved
                    out.append(value if ok else "")

            else:  # bind
                _, bkind, payload, right, raw = seg

                if bkind == "key":
                    resolved = cls._resolve_placeholder(user, payload)
                    if resolved is None or not resolved[0]:
                        continue
                    if "{" in right:
                        out.append(cls._render_placeholders(right, user))
                    else:
                        out.append(right + resolved[1])

                elif bkind == "cond":
                    if evaluate_node(user, payload):
                        out.append(cls._render_placeholders(right, user))

                else:  # error — оставляем как есть (не должно дойти после валидации)
                    out.append("{" + raw + "}")

        return "".join(out)

    @classmethod
    def _render_placeholders(cls, text: str, user: User) -> str:
        def repl(m: re.Match) -> str:
            resolved = cls._resolve_placeholder(user, m.group(1).strip())
            if resolved is None:
                return m.group(0)
            ok, value = resolved
            return value if ok else ""

        return re.sub(r"\{([^{}|]+)\}", repl, text)

    @staticmethod
    def _resolve_placeholder(user: User, key: str):
        """Возвращает (exists, value) или None, если ключ неизвестен."""
        key = key.strip()

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
