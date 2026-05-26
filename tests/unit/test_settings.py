from agent_scheduler.config.settings import env_file_path, load_settings


def test_env_file_path_uses_selected_env(tmp_path) -> None:
    assert env_file_path("dev", root=tmp_path) == tmp_path / ".env.dev"


def test_load_settings_from_selected_env_file(tmp_path, monkeypatch) -> None:
    monkeypatch.delenv("PREFECT_API_DATABASE_CONNECTION_URL", raising=False)
    env_file = tmp_path / ".env.dev"
    env_file.write_text(
        "\n".join(
            [
                "APP_ENV=dev",
                "PREFECT_API_URL=http://prefect-dev:4200/api",
                "PREFECT_API_DATABASE_CONNECTION_URL=postgresql+asyncpg://prefect:prefect@postgres:5432/prefect",
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

