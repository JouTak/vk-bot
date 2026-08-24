from __future__ import annotations

from loguru import logger
from sqlalchemy import inspect, text

from .event_registry import EVENT_REGISTRY


def sync_schema(engine) -> None:
    """Аддитивно синхронизирует схему БД с декларациями. Идемпотентно."""
    insp = inspect(engine)

    with engine.begin() as conn:
        if insp.has_table("users"):
            cols = {c["name"] for c in insp.get_columns("users")}

            if "created_at" not in cols:
                logger.info("schema_sync: ADD users.created_at")
                conn.execute(text(
                    "ALTER TABLE users ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP"
                ))

        for event_def in EVENT_REGISTRY.values():
            table_name = event_def.table_name

            if not insp.has_table(table_name):
                continue

            existing = {c["name"] for c in insp.get_columns(table_name)}

            for field_def in event_def.fields:
                if field_def.name in existing:
                    continue

                if field_def.type == "int":
                    sql_type = "INT"
                    default_sql = f"DEFAULT {int(field_def.default or 0)}"
                elif field_def.type == "bool":
                    sql_type = "TINYINT(1)"
                    default_sql = f"DEFAULT {1 if field_def.default else 0}"
                else:
                    sql_type = "VARCHAR(255)"
                    escaped = str(field_def.default or "").replace("'", "''")
                    default_sql = f"DEFAULT '{escaped}'"

                logger.info(f"schema_sync: ADD {table_name}.{field_def.name}")
                conn.execute(text(
                    f"ALTER TABLE {table_name} ADD COLUMN `{field_def.name}` "
                    f"{sql_type} NOT NULL {default_sql}"
                ))

        if insp.has_table("ignored_users"):
            cols = {c["name"] for c in insp.get_columns("ignored_users")}

            if "reason" not in cols:
                logger.info("schema_sync: ADD ignored_users.reason")
                conn.execute(text(
                    "ALTER TABLE ignored_users ADD COLUMN `reason` VARCHAR(255) NOT NULL DEFAULT ''"
                ))

    logger.info("schema_sync: done")