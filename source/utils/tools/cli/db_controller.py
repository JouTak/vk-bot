from __future__ import annotations
"""
DB controller (interactive TTY tool).

Features (minimal but practical):
- find: by ISU / by VK UID / by nickname substring
- show: base fields + short met summary (no full JSON dump by default)
- add: auto ISU, required uid, optional fio/grp/nck, optional met_json
- update: base fields + guided met editor (reuse logic from raw_edit style)
- delete: by ISU with confirmation

Run:
  python -m source.utils.tools.cli.db_controller
"""

import json
import sys
from dataclasses import dataclass
from textwrap import indent

import sqlalchemy as sa

from dotenv import load_dotenv

from source.utils.db.db import init_engine, session_scope
from source.utils.db.models import UserModel
from source.utils.db.repositories import UserDTO, UserRepository
from source.utils.tools.cli.common import get_vk_helper_from_env, vk_lookup_uid


def _is_tty() -> bool:
    return bool(sys.stdin and sys.stdin.isatty())


def _prompt(text: str, default: str | None = None) -> str:
    if default is None:
        try:
            return input(text).strip()
        except (EOFError, KeyboardInterrupt):
            raise KeyboardInterrupt
    try:
        v = input(f"{text} [{default}]: ").strip()
    except (EOFError, KeyboardInterrupt):
        raise KeyboardInterrupt
    return v if v else (default or "")


def _pause() -> None:
    if not _is_tty():
        return
    try:
        input("\nPress Enter to continue...")
    except (EOFError, KeyboardInterrupt):
        return


def _confirm(text: str, default_no: bool = True) -> bool:
    default = "N" if default_no else "Y"
    v = _prompt(f"{text} (y/N)" if default_no else f"{text} (Y/n)", default=default).strip().lower()
    if v == "":
        return not default_no
    return v in {"y", "yes"}


def _met_summary(met: dict) -> str:
    """Full met dump formatted for console: one event per line."""
    if not met:
        return "(no met)"

    def fmt(v) -> str:
        if isinstance(v, bool):
            return "1" if v else "0"
        return str(v)

    lines: list[str] = []
    for ev in sorted(met.keys()):
        m = met.get(ev)
        if not isinstance(m, dict):
            lines.append(f"{ev}={fmt(m)}")
            continue

        keys: list[str] = []
        for k in sorted(m.keys()):
            keys.append(f"{k}={fmt(m.get(k))}")
        lines.append(f"{ev}(" + ", ".join(keys) + ")")

    return "\n  " + "\n  ".join(lines)


def _print_user(dto: UserDTO) -> None:
    print("")
    print(f"isu: {dto.isu}")
    print(f"uid: {dto.uid}")
    print(f"fio: {dto.fio}")
    print(f"grp: {dto.grp}")
    print(f"nck: {dto.nck}")
    print("met:" + _met_summary(dto.met))


def _guided_met_edit(current: dict) -> dict:
    """
    Form-based met editor (no external deps).

    - Schema is taken from source.utils.storage.user_store.User.text2info[5]
    - For an event: asks ALL known fields sequentially.
      * Enter keeps current value
      * '-' clears the field
      * Values are validated/coerced to correct types
    - Allows adding/removing whole events.
    """
    from source.utils.storage.user_store import User as LegacyUser

    schema: dict[str, dict[str, object]] = LegacyUser.text2info[5]  # type: ignore[assignment]
    met = dict(current or {})

    def ensure_event(ev: str) -> dict:
        v = met.get(ev)
        if not isinstance(v, dict):
            v = {}
            met[ev] = v
        return v

    def parse_bool(raw: str) -> bool:
        raw = raw.strip().lower()
        if raw in ("1", "true", "yes", "y"):
            return True
        if raw in ("0", "false", "no", "n"):
            return False
        raise ValueError("bool_expected")

    def parse_int(raw: str) -> int:
        raw = raw.strip()
        if raw.lstrip("-").isdigit():
            return int(raw)
        raise ValueError("int_expected")

    def parse_str(raw: str) -> str:
        return raw

    def coerce(field_type, raw: str):
        if field_type is int:
            return parse_int(raw)
        if field_type is str:
            return parse_str(raw)
        # bool is encoded as a callable (s2b) in LegacyUser.text2info
        # detect by name or by trying parse_bool
        try:
            return parse_bool(raw)
        except ValueError:
            # fallback: keep as string
            raise

    def edit_event(ev: str) -> None:
        ev_schema = schema.get(ev)
        if not isinstance(ev_schema, dict):
            print("Unknown event")
            return
        ev_obj = ensure_event(ev)

        print("")
        print(f"Edit event: {ev}")
        print("-" * (11 + len(ev)))

        for key, typ in ev_schema.items():
            cur = ev_obj.get(key, "")
            cur_s = str(cur) if cur is not None else ""
            while True:
                try:
                    raw = _prompt(f"{key}", default=cur_s)
                    if raw == cur_s:
                        break
                    if raw.strip() == "-":
                        ev_obj.pop(key, None)
                        break
                    # empty means keep current (because default already printed)
                    if raw.strip() == "":
                        break

                    # special validation rules
                    if key == "tsp":
                        v = parse_int(raw)
                        if v <= 0:
                            raise ValueError("tsp_must_be_positive")
                        ev_obj[key] = v
                        break

                    # ints that should be >= 0 by semantics
                    if typ is int:
                        v = parse_int(raw)
                        if v < 0:
                            raise ValueError("int_must_be_non_negative")
                        ev_obj[key] = v
                        break

                    # strings (allow empty)
                    if typ is str:
                        ev_obj[key] = str(raw)
                        break

                    # bool-like
                    ev_obj[key] = parse_bool(raw)
                    break
                except ValueError as e:
                    print(f"Invalid value for {key}: {e}")

    def pick_event() -> str | None:
        events = list(schema.keys())
        if not events:
            return None
        print("")
        print("Events:")
        for i, ev in enumerate(events, start=1):
            print(f"  {i}) {ev}")
        print("  0) back")
        sel = _prompt("pick", default="0").strip()
        if sel == "0":
            return None
        if sel.isdigit() and 1 <= int(sel) <= len(events):
            return events[int(sel) - 1]
        return None

    while True:
        print("")
        print("met")
        print("---")
        print("Current:", _met_summary(met))
        print("  1) Edit event (form)")
        print("  2) Remove event")
        print("  3) Clear met")
        print("  0) Done")
        c = _prompt("> ", default="0").strip()

        if c in ("0", "q", "quit", "exit"):
            return met

        if c == "3":
            met = {}
            continue

        if c == "2":
            ev = pick_event()
            if not ev:
                continue
            if ev in met:
                del met[ev]
            continue

        if c == "1":
            ev = pick_event()
            if not ev:
                continue
            edit_event(ev)
            continue


def _find_menu() -> tuple[str, str] | None:
    print("")
    print("find")
    print("----")
    print("  1) by ISU")
    print("  2) by UID")
    print("  3) by NCK contains")
    print("  0) back")
    c = _prompt("> ", default="0")
    if c == "0":
        return None
    if c == "1":
        return ("isu", _prompt("isu", default="").strip())
    if c == "2":
        return ("uid", _prompt("uid", default="").strip())
    if c == "3":
        return ("nck", _prompt("nck contains", default="").strip())
    return None


def _choose_from_results(rows: list[UserModel]) -> int | None:
    if not rows:
        print("No matches")
        return None

    # Materialize needed scalars immediately (prevents DetachedInstanceError).
    items = [(int(r.isu), int(r.uid), str(r.fio or ""), str(r.grp or ""), str(r.nck or "")) for r in rows]

    if len(items) == 1:
        return items[0][0]

    from source.utils.tools.cli.picker import PickerItem, pick

    def clean(v: str) -> str:
        return (v or "").strip()

    picker_items: list[PickerItem[int]] = []
    for isu, uid, fio, grp, nck in items:
        picker_items.append(
            PickerItem(
                value=int(isu),
                cols=[
                    str(int(isu)),
                    str(int(uid)),
                    clean(fio),
                    clean(grp),
                    clean(nck),
                ],
            )
        )

    return pick(
        "Users",
        picker_items,
        page_size=20,
        footer="Enter: choose | Left/Right: page | q quit",
        header_cols=["ISU", "UID", "FIO", "GRP", "NCK"],
    )


def _validate_grp(v: str) -> bool:
    if v == "":
        return True
    return len(v) == 5 and v[0].isalpha() and v[0].isupper() and v[1:].isdigit()




def _next_special_isu() -> int:
    with session_scope() as s:
        taken = set(
            int(x)
            for x in s.execute(sa.select(UserModel.isu).where(UserModel.isu.between(1, 99999))).scalars().all()
        )
    n = 1
    while n in taken:
        n += 1
    return n


def _validate_isu_for_add(isu_raw: str) -> int:
    isu_raw = isu_raw.strip()
    if isu_raw == "":
        return _next_special_isu()
    if not isu_raw.isdigit():
        raise ValueError("isu_not_int")
    isu = int(isu_raw)
    if not (100000 <= isu <= 999999):
        raise ValueError("isu_out_of_range")
    with session_scope() as s:
        exists = s.execute(sa.select(sa.func.count()).select_from(UserModel).where(UserModel.isu == isu)).scalar_one()
    if int(exists) > 0:
        raise ValueError("isu_already_exists")
    return isu


def _prompt_isu_for_add() -> int:
    while True:
        try:
            v = _prompt("isu (empty = special)", default="")
            if v.strip() == "":
                # extra confirmation for special ISU
                if not _confirm("Use special isu (1..99999)?", default_no=False):
                    continue
            return _validate_isu_for_add(v)
        except ValueError as e:
            print(f"Invalid isu: {e}")
        except KeyboardInterrupt:
            raise


def _prompt_uid_validated(vk) -> int:
    while True:
        try:
            raw = _prompt("uid (vk id)", default="")
            if not raw.lstrip("-").isdigit():
                print("Invalid uid: not an int")
                continue
            uid = int(raw)
            if uid <= 0:
                print("Invalid uid: must be > 0")
                continue
            r = vk_lookup_uid(vk, uid)
            v = _prompt(f"Found: {r.fio} ({r.url}). Is this correct? (Y/n)", default="Y").strip().lower()
            if v in ("", "y", "yes"):
                return uid
        except ValueError:
            print("Invalid uid: VK user not found")
        except RuntimeError:
            print("VK API is unreachable (proxy/network).")
            v = _prompt("Continue without VK check? (y/N)", default="N").strip().lower()
            if v in ("y", "yes"):
                # accept numeric uid without verification
                return uid
        except KeyboardInterrupt:
            raise


def _prompt_grp_validated() -> str:
    while True:
        try:
            grp = _prompt("grp (A1234 or empty)", default="").strip()
            if _validate_grp(grp):
                return grp
            print("Invalid grp format")
        except KeyboardInterrupt:
            raise


def main() -> None:
    if not _is_tty():
        raise SystemExit("db_controller requires an interactive terminal (stdin is not a TTY)")

    # Load .env but DO NOT override environment variables (PyCharm Run/Debug env vars win).
    load_dotenv(override=False)

    vk = get_vk_helper_from_env()
    if vk is None:
        raise SystemExit("VK is not configured: set BOT_TOKEN and GROUP_ID in env/.env")

    init_engine()

    while True:
        print("")
        print("Users DB")
        print("--------")
        print("  1) Find / view")
        print("  2) Add")
        print("  3) Update")
        print("  4) Delete")
        print("  0) Back")
        try:
            choice = _prompt("> ", default="0")
        except KeyboardInterrupt:
            return

        if choice in {"0", "q", "quit", "exit"}:
            return

        if choice == "1":
            q = _find_menu()
            if not q:
                continue
            kind, val = q
            if not val:
                continue

            # IMPORTANT: materialize scalars inside session_scope to avoid DetachedInstanceError.
            with session_scope() as s:
                if kind == "isu" and val.isdigit():
                    items = (
                        s.execute(
                            sa.select(UserModel.isu, UserModel.uid, UserModel.fio, UserModel.grp, UserModel.nck).where(
                                UserModel.isu == int(val)
                            )
                        )
                        .all()
                    )
                elif kind == "uid" and val.lstrip("-").isdigit():
                    items = (
                        s.execute(
                            sa.select(UserModel.isu, UserModel.uid, UserModel.fio, UserModel.grp, UserModel.nck).where(
                                UserModel.uid == int(val)
                            )
                        )
                        .all()
                    )
                else:
                    items = (
                        s.execute(
                            sa.select(UserModel.isu, UserModel.uid, UserModel.fio, UserModel.grp, UserModel.nck).where(
                                UserModel.nck.like(f"%{val}%")
                            )
                        )
                        .all()
                    )

            # Convert rows to the same shape expected by the chooser (list of tuples).
            rows = [
                UserModel(isu=int(isu), uid=int(uid), fio=str(fio or ""), grp=str(grp or ""), nck=str(nck or ""))
                for isu, uid, fio, grp, nck in items
            ]
            isu = _choose_from_results(rows)
            if isu is not None:
                with session_scope() as s:
                    dto = UserRepository(s).get(int(isu))
                if dto:
                    _print_user(dto)
                    _pause()
            continue

        if choice == "2":
            try:
                isu = _prompt_isu_for_add()
                uid = _prompt_uid_validated(vk)
                fio_default = vk_lookup_uid(vk, uid).fio
                fio = _prompt("fio", default=fio_default).strip()
                grp = _prompt_grp_validated()
                nck = _prompt("nck (empty allowed)", default="").strip()
                met_choice = _prompt("met: Enter=empty, 1=edit", default="").strip()
            except KeyboardInterrupt:
                return

            met: dict = {}
            if met_choice == "1":
                met = _guided_met_edit({})

            with session_scope() as s:
                dto = UserDTO(isu=isu, uid=uid, fio=fio, grp=grp, nck=nck, met=met)
                UserRepository(s).upsert(dto)
            print(f"Added isu={isu}")
            _pause()
            continue

        if choice == "3":
            while True:
                try:
                    isu = _prompt("isu", default="").strip()
                except KeyboardInterrupt:
                    return
                if isu.isdigit():
                    break
                print("Invalid isu: must be integer")
            isu_i = int(isu)
            with session_scope() as s:
                repo = UserRepository(s)
                dto = repo.get(isu_i)
                if not dto:
                    print("Not found")
                    _pause()
                    continue
                _print_user(dto)

            # uid: try VK validation first, fallback to numeric uid if VK unreachable
            while True:
                try:
                    uid_raw = _prompt("uid (vk id)", default=str(dto.uid)).strip()
                except KeyboardInterrupt:
                    return
                if not uid_raw.lstrip("-").isdigit():
                    print("Invalid uid: not an int")
                    continue
                uid_int = int(uid_raw)
                if uid_int <= 0:
                    print("Invalid uid: must be > 0")
                    continue
                try:
                    r = vk_lookup_uid(vk, uid_int)
                    ok = _prompt(f"Found: {r.fio} ({r.url}). Is this correct? (Y/n)", default="Y").strip().lower()
                    if ok not in ("", "y", "yes"):
                        continue
                except RuntimeError:
                    ok = _prompt("VK API unreachable. Use uid without check? (y/N)", default="N").strip().lower()
                    if ok not in ("y", "yes"):
                        continue
                break

            # fio: default to VK fio if it differs and user confirms
            try:
                fio = _prompt("fio", default=dto.fio).strip()
            except KeyboardInterrupt:
                return

            # grp: enforce A1234 or empty
            grp = _prompt_grp_validated()

            try:
                nck = _prompt("nck", default=dto.nck).strip()
            except KeyboardInterrupt:
                return

            met = dto.met
            try:
                met_choice = _prompt("met: Enter=keep, 1=edit", default="").strip()
            except KeyboardInterrupt:
                return
            if met_choice == "1":
                met = _guided_met_edit(dto.met)

            dto2 = UserDTO(
                isu=isu_i,
                uid=uid_int,
                fio=fio,
                grp=grp,
                nck=nck,
                met=met,
            )
            with session_scope() as s:
                UserRepository(s).upsert(dto2)
            print("Updated")
            _pause()
            continue

        if choice == "4":
            while True:
                try:
                    isu = _prompt("isu", default="").strip()
                except KeyboardInterrupt:
                    return
                if isu.isdigit():
                    break
                print("Invalid isu: must be integer")
            isu_i = int(isu)
            with session_scope() as s:
                dto = UserRepository(s).get(isu_i)
            if not dto:
                print("Not found")
                _pause()
                continue
            _print_user(dto)
            try:
                if not _confirm("Delete this user?", default_no=True):
                    continue
            except KeyboardInterrupt:
                return
            with session_scope() as s:
                s.execute(sa.delete(UserModel).where(UserModel.isu == isu_i))
            print("Deleted")
            _pause()
            continue


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass