from __future__ import annotations

import os
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


AppEnv = Literal["local", "dev", "prod"]


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore", populate_by_name=True)

    app_env: AppEnv = Field(default="local", alias="APP_ENV")
    prefect_api_url: str = Field(
        default="http://127.0.0.1:4200/api",
        alias="PREFECT_API_URL",
    )
    prefect_api_database_connection_url: str = Field(
        alias="PREFECT_API_DATABASE_CONNECTION_URL",
    )
    agent_scheduler_global_concurrency: int = Field(
        default=2,
        ge=1,
        alias="AGENT_SCHEDULER_GLOBAL_CONCURRENCY",
    )


def env_file_path(env: str, root: Path | None = None) -> Path:
    base_path = root or Path.cwd()
    return base_path / f".env.{env}"


def load_settings(env: str | None = None, root: Path | None = None) -> AppSettings:
    selected_env = env or os.getenv("APP_ENV", "local")
    env_file = env_file_path(selected_env, root=root)
    return AppSettings(app_env=selected_env, _env_file=env_file if env_file.exists() else None)


def apply_prefect_environment(settings: AppSettings) -> None:
    os.environ["PREFECT_API_URL"] = settings.prefect_api_url
    os.environ["PREFECT_API_DATABASE_CONNECTION_URL"] = (
        settings.prefect_api_database_connection_url
    )
