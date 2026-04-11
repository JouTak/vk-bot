from __future__ import annotations
"""
Interactive console menu for project maintenance tasks.

Run:
  python -m source.utils.tools.console
"""

import os
import subprocess
import sys
from typing import Callable

from dotenv import load_dotenv


def _run_module(module: str, args: list[str] | None = None) -> int:
    if args is None:
        args = []
    cmd = [sys.executable, "-m", module, *args]
    print("\n>>>", " ".join(cmd))
    try:
        p = subprocess.run(cmd, check=False)
        return int(p.returncode)
    except KeyboardInterrupt:
        return 130


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


def _pause() -> None:
    # Only used for "viewer" commands. For actions we return to the menu immediately.
    if not sys.stdin or not sys.stdin.isatty():
        return
    try:
        input("\nPress Enter to continue...")
    except (EOFError, KeyboardInterrupt):
        return


def _header(title: str) -> None:
    print("\n" + title)
    print("-" * len(title))


def _main_menu() -> str:
    _header("VK Bot Tools")
    print("  1) Users DB                  | Find/add/update/delete users")
    print("  2) Import users.txt -> DB    | Parse legacy file and sync DB (+Fix panel)")
    print("  3) Reset DB                  | Drop DB tables (double confirm)")
    print("  4) Fix panel                 | Review/fix flagged rows (from users_raw_lines)")
    print("  5) DB stats                  | Quick summary + top fix reasons")
    print("  0) Exit                      | Quit")
    return _prompt("> ")


# NOTE: raw/stats submenus were removed to keep UX minimal.


def main() -> None:
    # Load .env for defaults (does not override existing environment).
    load_dotenv(override=False)

    # In some non-interactive environments stdin isn't available.
    # Exit early to avoid an infinite loop of "Неизвестная команда".
    if not sys.stdin or not sys.stdin.isatty():
        print(
            "VK Bot Tools (non-interactive mode)\n"
            "Run in a real terminal to use interactive menu:\n"
            "  python -m source.utils.tools.console\n\n"
            "Direct commands:\n"
            "  python -m source.utils.tools.cli.migrate_from_txt\n"
            "  python -m source.utils.tools.cli.reset_db\n"
            "  python -m source.utils.tools.cli.verify_import\n"
            "  python -m source.utils.tools.cli.raw_pick\n"
            "  python -m source.utils.tools.cli.db_stats\n"
        )
        return

    while True:
        try:
            choice = _main_menu()
        except KeyboardInterrupt:
            return

        if choice is None:
            return
        choice = str(choice).strip()
        if choice == "":
            continue
        if choice in ("0", "q", "quit", "exit"):
            return

        # 1) DB controller
        if choice == "1":
            rc = _run_module("source.utils.tools.cli.db_controller")
            if rc == 130:
                print("Cancelled")
            elif rc != 0:
                print(f"Error (exit_code={rc})")
                _pause()
            continue

        # 2) Migration
        if choice == "2":
            rc = _run_module("source.utils.tools.cli.migrate_from_txt", [])
            if rc != 0:
                print(f"Error (exit_code={rc})")
                _pause()
            continue

        # 3) Reset DB (double confirm)
        if choice == "3":
            if not _prompt("Are you sure? (Y/n)", default="Y").strip().lower() in ("", "y", "yes"):
                continue
            if not _prompt("Are you absolutely sure? (y/N)", default="N").strip().lower() in ("y", "yes"):
                continue
            db_url = os.getenv("DATABASE_URL") or ""
            if not db_url:
                print("Error: DATABASE_URL is not set")
                _pause()
                continue
            rc = _run_module("source.utils.tools.cli.reset_db", [])
            if rc != 0:
                print(f"Error (exit_code={rc})")
                _pause()
            continue

        # 4) Fix panel
        if choice == "4":
            rc = _run_module("source.utils.tools.cli.raw_pick")
            if rc == 130:
                print("Cancelled")
            elif rc != 0:
                print(f"Error (exit_code={rc})")
                _pause()
            continue

        # 5) DB stats
        if choice == "5":
            rc = _run_module("source.utils.tools.cli.db_stats")
            if rc != 0:
                print(f"Error (exit_code={rc})")
            _pause()
            continue

        # If user hit Ctrl+C inside a submenu, some terminals may leave an empty input behind.
        # Do not print "Unknown command" for empty input.
        if str(choice).strip() != "":
            print("Unknown command")
            _pause()


if __name__ == "__main__":
    main()
