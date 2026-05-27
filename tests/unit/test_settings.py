import os

from agent_scheduler.config.settings import (
    apply_prefect_environment,
    env_file_path,
    load_settings,
)


def test_env_file_path_uses_selected_env(tmp_path) -> None:
    assert env_file_path("dev", root=tmp_path) == tmp_path / ".env.dev"


def test_load_settings_from_selected_env_file(tmp_path, monkeypatch) -> None:
    monkeypatch.delenv("PREFECT_API_URL", raising=False)
    monkeypatch.delenv("PREFECT_API_DATABASE_CONNECTION_URL", raising=False)
    env_file = tmp_path / ".env.dev"
    env_file.write_text(
        "\n".join(
            [
                "APP_ENV=dev",
                "PREFECT_API_URL=http://prefect-dev:4200/api",
                "PREFECT_API_DATABASE_CONNECTION_URL=postgresql+asyncpg://prefect:prefect@postgres:5432/prefect",
                "AGENT_SCHEDULER_DATABASE_URL=postgresql+asyncpg://agent_scheduler_app:agent_scheduler@postgres:5432/agent_scheduler",
                "PIPELINE_DATABASE_URL=postgresql+asyncpg://pipeline_app:pipeline_app@postgres:5432/pipeline_data",
                "TRADING_PRIVATE_DATABASE_URL=postgresql+asyncpg://trading_private_writer:trading_private@postgres:5432/pipeline_data",
            ]
        )
    )

    settings = load_settings(env="dev", root=tmp_path)

    assert settings.app_env == "dev"
    assert settings.prefect_api_url == "http://prefect-dev:4200/api"
    assert (
        settings.prefect_api_database_connection_url
        == "postgresql+asyncpg://prefect:prefect@postgres:5432/prefect"
    )
    assert settings.agent_scheduler_database_url.endswith("@postgres:5432/agent_scheduler")
    assert settings.pipeline_database_url.endswith("@postgres:5432/pipeline_data")
    assert settings.trading_private_database_url.endswith("@postgres:5432/pipeline_data")


def test_apply_prefect_environment_sets_prefect_client_vars(tmp_path, monkeypatch) -> None:
    monkeypatch.delenv("PREFECT_API_URL", raising=False)
    monkeypatch.delenv("PREFECT_API_DATABASE_CONNECTION_URL", raising=False)
    monkeypatch.delenv("AGENT_SCHEDULER_DATABASE_URL", raising=False)
    monkeypatch.delenv("PIPELINE_DATABASE_URL", raising=False)
    monkeypatch.delenv("TRADING_PRIVATE_DATABASE_URL", raising=False)
    env_file = tmp_path / ".env.local"
    env_file.write_text(
        "\n".join(
            [
                "APP_ENV=local",
                "PREFECT_API_URL=http://127.0.0.1:4200/api",
                "PREFECT_API_DATABASE_CONNECTION_URL=postgresql+asyncpg://prefect:prefect@postgres:5432/prefect",
            ]
        )
    )
    settings = load_settings(env="local", root=tmp_path)

    apply_prefect_environment(settings)

    assert os.environ["PREFECT_API_URL"] == "http://127.0.0.1:4200/api"
    assert os.environ["PREFECT_API_DATABASE_CONNECTION_URL"].startswith("postgresql+asyncpg://")
    assert os.environ["AGENT_SCHEDULER_DATABASE_URL"].endswith(
        "@postgres:5432/agent_scheduler"
    )
    assert os.environ["PIPELINE_DATABASE_URL"].endswith("@postgres:5432/pipeline_data")
    assert os.environ["TRADING_PRIVATE_DATABASE_URL"].endswith("@postgres:5432/pipeline_data")
