from __future__ import annotations
"""
Non-interactive smoke tests for DB tools.

Goal:
- catch obvious breakages after DB migration (tables missing, wrong imports, etc.)
- can be run in CI and locally

Run:
  python -m source.utils.tools.cli._smoke_test

It does NOT test interactive TTY tools (console/raw_pick/raw_edit/db_controller).
"""

import os

from dotenv import load_dotenv

from source.utils.tools.cli import db_stats, migrate_from_txt, verify_import


def main() -> None:
    load_dotenv(override=False)
    db_url = os.getenv("DATABASE_URL", "")
    if not db_url:
        raise SystemExit("DATABASE_URL is not set")

    # Ensure import does not crash and creates tables
    migrate_from_txt.main()

    # Ensure verify works after import
    verify_import.main()

    # Ensure stats works
    db_stats.main()

    print("smoke_test: OK")


if __name__ == "__main__":
    main()