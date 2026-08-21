from __future__ import annotations
from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # VK
    bot_token: str
    group_id: int

    # DB
    database_url: str
    use_database: bool = True

    # Admins — из env, НЕ из кода
    admin_ids: list[int] = []

    # Feature flags
    enable_migration: bool = False

    # Logging
    log_level: str = "INFO"
    log_path: str = "/app/data/py.log"

    # Paths
    base_dir: Path = Path(__file__).resolve().parent.parent

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


settings = Settings()