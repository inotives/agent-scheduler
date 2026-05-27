from typer.testing import CliRunner

from agent_scheduler.cli import app


def test_cli_help() -> None:
    result = CliRunner().invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "Schedule headless agent workflows" in result.output
    assert "pipeline" not in result.output


def test_cli_health_json() -> None:
    result = CliRunner().invoke(app, ["health"])

    assert result.exit_code == 0
    assert result.output.strip() == '{"status": "ok"}'
