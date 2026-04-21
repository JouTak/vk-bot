from __future__ import annotations
"""
Interactive raw row editor for users_raw_lines.

Goal: make manual correction максимально наглядной и быстрой:
- показать raw строку + текущие распарсенные поля + ошибку
- предложить редактировать поля по одному (enter = оставить как есть)
- для met_json: поддержка многострочного ввода (вставка JSON) + валидация
- после сохранения сразу предложить "apply" (импорт в нормализованные таблицы)
- после apply сразу предложить открыть следующую проблемную строку

Run:
  python -m source.utils.tools.cli.raw_edit <raw_id>
"""

import argparse
import json
import sys
from textwrap import indent

import sqlalchemy as sa

from source.utils.db.db import init_engine, session_scope
from source.utils.db.models import UsersRawLineModel
from source.utils.tools.cli.common import get_vk_helper_from_env, vk_lookup_uid
from source.utils.tools.cli.raw_fixes import cmd_apply


def _is_tty() -> bool:
    return bool(sys.stdin and sys.stdin.isatty())


def _prompt(text: str, default: str | None = None) -> str:
    if default is None:
        try:
            return input(text).strip()
        except EOFError:
            return ""
    try:
        v = input(f"{text} [{default}]: ").strip()
    except EOFError:
        return default
    return v if v else default


def _prompt_int_keep(name: str, current: int | None) -> int | None:
    """Prompt int, Enter keeps current."""
    v = _prompt(name, default="" if current is None else str(current))
    v = v.strip()
    if v == "":
        return current
    if v.lower() in {"none", "null", "-"}:
        return None
    if v.lstrip("-").isdigit():
        return int(v)
    print("  ! not an int; keeping current")
    return current


def _prompt_int_edit(name: str) -> int | None:
    """Prompt int for editing: default is empty; Enter means empty/clear (returns None)."""
    v = _prompt(f"{name}", default="").strip()
    if v == "":
        return None
    if v.lstrip("-").isdigit():
        return int(v)
    print("  ! not an int")
    return None


def _prompt_str_keep(name: str, current: str) -> str:
    """Prompt str, Enter keeps current."""
    v = _prompt(name, default=current or "")
    return v


def _prompt_str_edit(name: str) -> str:
    """Prompt str for editing: default is empty; Enter means empty/clear."""
    v = _prompt(f"{name}", default="")
    return v.strip()




def _prompt_json_multiline(current: str) -> str:
    """
    Met JSON editor (no external deps).

    UX goals:
    - show pretty JSON
    - offer guided editing for common fields (met.<event>.<key>)
    - allow quick paste/replace for advanced cases

    Keys:
      Enter  - keep
      1      - guided editor (pick event -> pick field -> set value)
      2      - paste full JSON (multiline, END to finish)
      3      - clear
    """
    # Parse current JSON (best-effort)
    obj: dict[str, object] = {}
    if current.strip():
        try:
            parsed = json.loads(current)
            if isinstance(parsed, dict):
                obj = parsed
        except Exception:
            obj = {}

    def pretty_print() -> None:
        print("\nmet_json:")
        if obj:
            print(indent(json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True), "  "))
        else:
            print("  (empty)")

    def set_path(d: dict, path: list[str], value: object) -> None:
        cur = d
        for key in path[:-1]:
            nxt = cur.get(key)
            if not isinstance(nxt, dict):
                nxt = {}
                cur[key] = nxt
            cur = nxt
        cur[path[-1]] = value

    def get_event_keys() -> list[str]:
        keys = [k for k, v in obj.items() if isinstance(v, dict)]
        # stable order, common events first
        common = ["a24", "s25", "y25", "a25"]
        ordered = [k for k in common if k in keys] + [k for k in sorted(keys) if k not in common]
        return ordered

    def guided() -> None:
        # Event pick
        events = get_event_keys()
        if not events:
            ev = _prompt("event key (e.g. a24)", default="")
            if not ev:
                return
            if ev not in obj or not isinstance(obj.get(ev), dict):
                obj[ev] = {}
            events = [ev]

        print("\nEvents:")
        for i, ev in enumerate(events, start=1):
            print(f"  {i}) {ev}")
        ev_idx = _prompt("pick event", default="1")
        if not ev_idx.isdigit() or not (1 <= int(ev_idx) <= len(events)):
            return
        ev = events[int(ev_idx) - 1]
        ev_obj = obj.get(ev)
        if not isinstance(ev_obj, dict):
            ev_obj = {}
            obj[ev] = ev_obj

        # Field pick
        fields = sorted(list(ev_obj.keys()))
        print("\nFields:")
        if fields:
            for i, k in enumerate(fields, start=1):
                print(f"  {i}) {k} = {ev_obj.get(k)}")
        else:
            print("  (no fields)")
        print("  n) new field")

        f_sel = _prompt("pick field", default="n" if not fields else "1").strip().lower()
        if f_sel == "n":
            fk = _prompt("field name", default="").strip()
            if not fk:
                return
        else:
            if not f_sel.isdigit() or not (1 <= int(f_sel) <= len(fields)):
                return
            fk = fields[int(f_sel) - 1]

        cur_val = ev_obj.get(fk, "")
        raw = _prompt("value (type: int/bool/str; empty clears)", default=str(cur_val) if cur_val is not None else "")
        if raw == "":
            # clear field
            ev_obj.pop(fk, None)
            return

        # best-effort typing
        if raw.lower() in {"true", "false"}:
            val: object = raw.lower() == "true"
        elif raw.lstrip("-").isdigit():
            val = int(raw)
        else:
            val = raw
        set_path(obj, [ev, fk], val)

    while True:
        pretty_print()
        mode = _prompt("met_json edit [Enter=keep, 1=guided, 2=paste, 3=clear]", default="").strip().lower()
        if mode == "":
            return json.dumps(obj, ensure_ascii=False) if obj else (current if current.strip() else "")
        if mode == "3":
            return ""
        if mode == "2":
            print("Paste JSON (multi-line). Finish with a line containing only: END")
            lines: list[str] = []
            while True:
                try:
                    ln = input()
                except (EOFError, KeyboardInterrupt):
                    break
                if ln.strip() == "END":
                    break
                lines.append(ln)
            raw = "\n".join(lines).strip()
            if raw == "":
                obj = {}
                continue
            parsed = json.loads(raw)
            if not isinstance(parsed, dict):
                raise json.JSONDecodeError("met_json must be an object", raw, 0)
            obj = parsed
            continue
        if mode == "1":
            guided()
            continue
        # unknown -> loop


def _print_row(row: UsersRawLineModel) -> None:
    print("\nRAW ROW")
    print("-------")
    print(f"id:      {row.id}")
    print(f"line_no: {row.line_no}")
    print(f"status:  {row.status}")
    if row.error:
        print(f"error:   {row.error}")
    print("")
    print("raw_line:")
    print(indent(row.raw_line or "", "  "))
    print("")
    print("parsed fields:")
    print(f"  isu: {row.isu}")
    print(f"  uid: {row.uid}")
    print(f"  fio: {row.fio}")
    print(f"  grp: {row.grp}")
    print(f"  nck: {row.nck}")


def _next_problem_id(after_line_no: int, after_id: int) -> int | None:
    """Find next row with status != ok after (line_no, id)."""
    with session_scope() as s:
        rid = (
            s.execute(
                sa.select(UsersRawLineModel.id)
                .where(UsersRawLineModel.status != "ok")
                .where(
                    sa.or_(
                        UsersRawLineModel.line_no > after_line_no,
                        sa.and_(
                            UsersRawLineModel.line_no == after_line_no,
                            UsersRawLineModel.id > after_id,
                        ),
                    )
                )
                .order_by(UsersRawLineModel.line_no, UsersRawLineModel.id)
                .limit(1)
            )
            .scalar_one_or_none()
        )
        return int(rid) if rid is not None else None


def edit_one(raw_id: int) -> None:
    # VK API for UID validation (shared helper).
    vk = get_vk_helper_from_env()

    init_engine()

    def issues_for_row(row: UsersRawLineModel) -> dict[str, str]:
        """
        Returns field -> human readable issue.
        Only ISU is considered a hard requirement by project rules.
        Other fields may be "non-ideal" but still allowed.
        """
        issues: dict[str, str] = {}

        # ISU rules:
        # - university isu: 100000..999999
        # - special_isu: 1..99999 (when student has no ITMO isu)
        isu = row.isu
        if isu is None:
            issues["isu"] = "ISU is missing (set ITMO isu 100000..999999 or special_isu 1..99999)"
        else:
            isu = int(isu)
            if isu == 0 or isu < 0:
                issues["isu"] = "ISU must be positive (ITMO 100000..999999 or special_isu 1..99999)"
            elif 1 <= isu <= 99999:
                # ok: special_isu
                pass
            elif 100000 <= isu <= 999999:
                # ok: regular isu
                pass
            else:
                issues["isu"] = "ISU must be 100000..999999 or special_isu 1..99999"

        # uid: allowed to be 0/1 (valid but not usable for sender); show as issue to fix optionally
        if row.uid is None:
            issues["uid"] = "UID is missing (VK numeric id). 0/1 are allowed but sender will skip them."
        else:
            uid = int(row.uid)
            if 0 <= uid <= 1:
                issues["uid"] = "UID is 0/1 (allowed, but sender will skip such users)"

        # grp: show if does not match the typical format, but do not block
        grp = (row.grp or "").strip()
        if grp:
            if len(grp) != 5 or not ("A" <= grp[0] <= "Z") or not grp[1:].isdigit():
                issues["grp"] = "GRP format is unusual (expected A-Z + 4 digits, e.g. M3201)"

        # fio: common expected format, but do not block
        fio = (row.fio or "").strip()
        if fio:
            parts = [p for p in fio.split() if p]
            if len(parts) != 3:
                issues["fio"] = 'FIO format is unusual (often "Фамилия Имя Отчество")'

        # nck: preferred format is [A-Za-z0-9_]+, no spaces.
        nck = (row.nck or "").strip()
        if nck:
            if " " in nck:
                issues["nck"] = "NCK contains spaces (preferred: only A-Za-z0-9 and '_' without spaces)"
            else:
                for ch in nck:
                    if not (("a" <= ch.lower() <= "z") or ("0" <= ch <= "9") or ch == "_"):
                        issues["nck"] = "NCK contains invalid chars (preferred: only A-Za-z0-9 and '_' without spaces)"
                        break
        if len(nck) > 64:
            # keep as separate note; overwrite only if no other nck issue detected
            issues.setdefault("nck", "NCK is very long (>64)")

        # met_json: validated by JSON parser later
        return issues

    with session_scope() as s:
        row = s.get(UsersRawLineModel, raw_id)
        if not row:
            raise SystemExit(f"raw row id={raw_id} not found")

        _print_row(row)

        issues = issues_for_row(row)
        if issues:
            print("\nDetected issues:")
            for k, msg in issues.items():
                print(f"  - {k}: {msg}")
        else:
            print("\nDetected issues: none")

        print("\nEDIT (press Enter to keep current value)")

        # Edit only fields that are currently problematic (plus met_json if JSON is broken).
        # ISU is always forced to be valid before saving.
        if "isu" in issues:
            while True:
                v = _prompt_int_edit("isu")
                # Enter = clear -> invalid for ISU (must be set)
                if v is None:
                    print("  ! isu cannot be empty")
                    continue
                new_isu = v
                row.isu = new_isu
                issues = issues_for_row(row)
                if "isu" not in issues:
                    break
                print(f"  ! {issues['isu']}")
        else:
            new_isu = row.isu

        if "uid" in issues:
            # If current uid is already 0/1 and user keeps it by entering 0/1,
            # it is allowed (sender will skip) and we should not VK-check it.
            #
            # If user provides uid > 1, validate via VK API (if available).
            while True:
                v = _prompt_int_edit("uid")
                if v is None:
                    # Enter clears, but uid cannot be empty
                    print("  ! uid cannot be empty")
                    continue

                if 0 <= int(v) <= 1:
                    new_uid = int(v)
                    break

                # For normal UIDs, try VK validation (same semantics as db_controller).
                if vk is None:
                    print("  ! VK API is unavailable (missing env or init error).")
                    ans = _prompt("Continue without VK check? (y/N)", default="N").strip().lower()
                    if ans in ("y", "yes"):
                        new_uid = int(v)
                        break
                    continue

                try:
                    r = vk_lookup_uid(vk, int(v))
                    ans = _prompt(f"Found: {r.fio} ({r.url}). Is this correct? (Y/n)", default="Y").strip().lower()
                    if ans in ("", "y", "yes"):
                        new_uid = int(v)
                        break
                    continue
                except ValueError:
                    print("  ! Invalid uid: VK user not found")
                    continue
                except RuntimeError:
                    print("  ! VK API is unreachable/unavailable.")
                    ans = _prompt("Continue without VK check? (y/N)", default="N").strip().lower()
                    if ans in ("y", "yes"):
                        new_uid = int(v)
                        break
                    continue
        else:
            new_uid = row.uid

        if "fio" in issues:
            new_fio = _prompt_str_edit("fio")  # Enter => ""
        else:
            new_fio = row.fio or ""

        if "grp" in issues:
            new_grp = _prompt_str_edit("grp")  # Enter => ""
        else:
            new_grp = row.grp or ""

        if "nck" in issues:
            new_nck = _prompt_str_edit("nck")  # Enter => ""
        else:
            new_nck = row.nck or ""

        # met_json: ask only if it's problematic (invalid JSON) OR user explicitly wants to edit it.
        need_met = False
        if row.met_json and row.met_json.strip():
            try:
                json.loads(row.met_json)
            except Exception:
                need_met = True

        if need_met:
            print("\nmet_json is invalid JSON, please fix it.")
            while True:
                try:
                    new_met = _prompt_json_multiline(row.met_json or "")
                    break
                except json.JSONDecodeError as e:
                    print(f"  ! JSON error: {e}")
                    print("  Try again.")
        else:
            # met_json is valid; do not ask to edit it in fix panel
            new_met = row.met_json or ""

        # Apply changes. Do NOT reset status/error here:
        # the row should disappear from fix panel only after it passes cmd_apply()
        # which contains the "source-of-truth" validation for raw lines.
        row.isu = new_isu
        row.uid = new_uid
        row.fio = new_fio
        row.grp = new_grp
        row.nck = new_nck
        row.met_json = new_met

    print("\nsaved")

    do_apply = _prompt("Apply now? (y/N)", default="N").lower().strip() in {"y", "yes"}
    if do_apply:
        cmd_apply(int(raw_id))

    jump_next = _prompt("Open next problem row? (Y/n)", default="Y").lower().strip() in {"", "y", "yes"}
    if jump_next:
        with session_scope() as s:
            row = s.get(UsersRawLineModel, raw_id)
            if not row:
                return
            nxt = _next_problem_id(int(row.line_no), int(row.id))
        if nxt is not None:
            edit_one(int(nxt))
        else:
            print("no more problem rows")


def main() -> None:
    if not _is_tty():
        raise SystemExit("raw_edit requires an interactive terminal (stdin is not a TTY)")

    p = argparse.ArgumentParser()
    p.add_argument("id", type=int)
    args = p.parse_args()
    try:
        edit_one(int(args.id))
    except KeyboardInterrupt:
        return


if __name__ == "__main__":
    main()