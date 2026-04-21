from __future__ import annotations

import argparse
import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, text


def main() -> None:
    # Load env vars from local .env if present (does not override existing env)
    load_dotenv(override=False)

    parser = argparse.ArgumentParser()
    # Intentionally no --db-url: DATABASE_URL must always be taken from environment/.env
    parser.parse_args()

    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise SystemExit("DATABASE_URL is not set")

    e = create_engine(db_url)

    with e.begin() as c:
        c.execute(text("SET FOREIGN_KEY_CHECKS=0"))
        # drop children first
        c.execute(text("DROP TABLE IF EXISTS user_a24"))
        c.execute(text("DROP TABLE IF EXISTS user_s25"))
        c.execute(text("DROP TABLE IF EXISTS user_y25"))
        c.execute(text("DROP TABLE IF EXISTS user_a25"))
        c.execute(text("DROP TABLE IF EXISTS ignored_users"))
        c.execute(text("DROP TABLE IF EXISTS kv_store"))
        c.execute(text("DROP TABLE IF EXISTS users_raw_lines"))
        c.execute(text("DROP TABLE IF EXISTS users"))
        c.execute(text("SET FOREIGN_KEY_CHECKS=1"))

    print("dropped")


if __name__ == "__main__":
    main()
