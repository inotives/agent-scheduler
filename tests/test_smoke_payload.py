import json
from pathlib import Path

from typer.testing import CliRunner

from agent_scheduler.cli import app
from agent_scheduler.schedules.types import WorkflowDeploymentSpec


ROOT = Path(__file__).resolve().parents[1]
SMOKE_PAYLOAD = ROOT / "examples" / "opencode_smoke.json"


def test_smoke_payload_matches_agent_smoke_contract() -> None:
    payload = json.loads(SMOKE_PAYLOAD.read_text(encoding="utf-8"))

    spec = WorkflowDeploymentSpec.model_validate(payload)

    assert spec.name == "opencode-smoke"
    assert spec.workflow_name == "agent_smoke"
    assert spec.runner is None


def test_smoke_payload_runs_with_fake_runner() -> None:
    result = CliRunner().invoke(app, ["run-now", "--payload", str(SMOKE_PAYLOAD), "--fake"])

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["ok"] is True
    assert payload["result"]["status"] == "succeeded"
    assert "\"task_name\":\"agent_smoke\"" in payload["result"]["stdout"]
    assert "\"runner\":\"opencode\"" in payload["result"]["stdout"]
