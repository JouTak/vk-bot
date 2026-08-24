from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # VK
    bot_token: str
    group_id: int

    # DB
    database_url: str

    # Admins
    admin_ids: list[int] = Field(default_factory=list)

    # Feature flags
    enable_migration: bool = False

    # Logging
    log_level: str = "INFO"
    log_path: str = "/app/data/py.log"

    # Paths
    base_dir: Path = Path(__file__).resolve().parents[1]

    model_config = SettingsConfigDict(
        env_file=base_dir / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()