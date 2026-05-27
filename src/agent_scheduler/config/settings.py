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
    agent_scheduler_database_url: str = Field(
        default=(
            "postgresql+asyncpg://agent_scheduler_app:"
            "agent_scheduler@postgres:5432/agent_scheduler"
        ),
        alias="AGENT_SCHEDULER_DATABASE_URL",
    )
    pipeline_database_url: str = Field(
        default="postgresql+asyncpg://pipeline_app:pipeline_app@postgres:5432/pipeline_data",
        alias="PIPELINE_DATABASE_URL",
    )
    trading_private_database_url: str = Field(
        default=(
            "postgresql+asyncpg://trading_private_writer:"
            "trading_private@postgres:5432/pipeline_data"
        ),
        alias="TRADING_PRIVATE_DATABASE_URL",
    )
    coingecko_api_base_url: str = Field(
        default="https://api.coingecko.com/api/v3",
        alias="COINGECKO_API_BASE_URL",
    )
    coingecko_api_key: str | None = Field(
        default=None,
        alias="COINGECKO_API_KEY",
    )
    coingecko_api_key_header: str = Field(
        default="x-cg-pro-api-key",
        alias="COINGECKO_API_KEY_HEADER",
    )
    coingecko_request_timeout_seconds: float = Field(
        default=30.0,
        gt=0,
        alias="COINGECKO_REQUEST_TIMEOUT_SECONDS",
    )
    coingecko_paginated_request_delay_seconds: float = Field(
        default=6.0,
        ge=0,
        alias="COINGECKO_PAGINATED_REQUEST_DELAY_SECONDS",
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
    os.environ["AGENT_SCHEDULER_DATABASE_URL"] = settings.agent_scheduler_database_url
    os.environ["PIPELINE_DATABASE_URL"] = settings.pipeline_database_url
    os.environ["TRADING_PRIVATE_DATABASE_URL"] = settings.trading_private_database_url
    os.environ["COINGECKO_API_BASE_URL"] = settings.coingecko_api_base_url
    os.environ["COINGECKO_API_KEY_HEADER"] = settings.coingecko_api_key_header
    os.environ["COINGECKO_REQUEST_TIMEOUT_SECONDS"] = str(
        settings.coingecko_request_timeout_seconds
    )
    os.environ["COINGECKO_PAGINATED_REQUEST_DELAY_SECONDS"] = str(
        settings.coingecko_paginated_request_delay_seconds
    )
    if settings.coingecko_api_key is not None:
        os.environ["COINGECKO_API_KEY"] = settings.coingecko_api_key
