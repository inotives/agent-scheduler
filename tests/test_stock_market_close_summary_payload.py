import json
from pathlib import Path

from typer.testing import CliRunner

from agent_scheduler.cli import app
from agent_scheduler.schedules.types import WorkflowDeploymentSpec


ROOT = Path(__file__).resolve().parents[1]
STOCK_MARKET_CLOSE_SUMMARY_PAYLOAD = (
    ROOT / "examples" / "stock_market_close_summary_daily.json"
)


def test_stock_market_close_summary_payload_matches_workflow_contract() -> None:
    payload = json.loads(
        STOCK_MARKET_CLOSE_SUMMARY_PAYLOAD.read_text(encoding="utf-8")
    )

    spec = WorkflowDeploymentSpec.model_validate(payload)

    assert spec.name == "daily-stock-market-close-summary"
    assert spec.workflow_name == "run_prompt"
    assert spec.schedule.type == "cron"
    assert spec.runner is None


def test_stock_market_close_summary_payload_runs_with_fake_runner() -> None:
    result = CliRunner().invoke(
        app,
        ["run-now", "--payload", str(STOCK_MARKET_CLOSE_SUMMARY_PAYLOAD), "--fake"],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["ok"] is True
    assert payload["result"]["status"] == "succeeded"
    assert payload["result"]["stdout"].count("\"runner\":\"opencode\"") == 1
    assert "examples/flows/market_close_summary" in payload["result"]["stdout"]
    assert "GEMI" in payload["result"]["stdout"]
    assert "PLTR" in payload["result"]["stdout"]
    assert "2026-05-26" in payload["result"]["stdout"]
    assert "outputs/daily-stock-market-close-summary.done.json" in payload["result"]["stdout"]
