import json

from typer.testing import CliRunner

from agent_scheduler.cli import app


def test_config_check_loads_selected_env_file(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("PREFECT_API_DATABASE_CONNECTION_URL", raising=False)
    (tmp_path / ".env.dev").write_text(
        "\n".join(
            [
                "APP_ENV=dev",
                "PREFECT_API_URL=http://prefect-dev:4200/api",
                "PREFECT_API_DATABASE_CONNECTION_URL=postgresql+asyncpg://prefect:prefect@postgres:5432/prefect",
            ]
        )
    )

    result = CliRunner().invoke(app, ["config", "check", "--env", "dev"])

    assert result.exit_code == 0
    assert json.loads(result.output) == {
        "ok": True,
        "env": "dev",
        "prefect_api_url": "http://prefect-dev:4200/api",
        "prefect_database_configured": True,
        "agent_scheduler_database_configured": True,
        "pipeline_database_configured": True,
        "trading_private_database_configured": True,
        "coingecko_api_base_url": "https://api.coingecko.com/api/v3",
        "coingecko_api_key_configured": False,
    }


def test_config_check_reports_missing_required_database_url(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("PREFECT_API_DATABASE_CONNECTION_URL", raising=False)

    result = CliRunner().invoke(app, ["config", "check", "--env", "local"])

    assert result.exit_code == 1
    payload = json.loads(result.output)
    assert payload["ok"] is False
    assert payload["error"]["code"] == "invalid_config"
    assert payload["error"]["details"][0]["loc"] == ["PREFECT_API_DATABASE_CONNECTION_URL"]
