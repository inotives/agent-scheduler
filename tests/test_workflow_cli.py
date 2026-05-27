import json
from pathlib import Path
from uuid import UUID, uuid4

from typer.testing import CliRunner

from agent_scheduler.cli import app


runner = CliRunner()


def write_payload(tmp_path: Path) -> Path:
    payload = {
        "name": "daily-gemi-close",
        "workflow_name": "run_skill_for_assets",
        "schedule": {"type": "cron", "cron": "0 16 * * *", "timezone": "Asia/Singapore"},
        "params": {"path_to_skill": "/skills/market-close", "assets": ["GEMI"]},
        "runner": "codex",
    }
    path = tmp_path / "payload.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_deploy_outputs_json(monkeypatch, tmp_path) -> None:
    payload_path = write_payload(tmp_path)
    deployment_id = uuid4()
    calls = []

    def fake_deploy(spec, global_concurrency_limit=2):
        calls.append((spec, global_concurrency_limit))
        return deployment_id

    monkeypatch.setattr("agent_scheduler.cli.workflows._deploy_workflow", fake_deploy)

    result = runner.invoke(app, ["deploy", str(payload_path)])

    assert result.exit_code == 0
    assert json.loads(result.output) == {
        "ok": True,
        "deployment_id": str(deployment_id),
        "name": "daily-gemi-close",
    }
    assert calls[0][0].workflow_name == "run_skill_for_assets"
    assert calls[0][1] == 2


def test_schedule_create_uses_same_payload_contract(monkeypatch, tmp_path) -> None:
    payload_path = write_payload(tmp_path)
    deployment_id = uuid4()

    monkeypatch.setattr(
        "agent_scheduler.cli.workflows._deploy_workflow",
        lambda spec, global_concurrency_limit=2: deployment_id,
    )

    result = runner.invoke(app, ["schedule", "create", str(payload_path)])

    assert result.exit_code == 0
    assert json.loads(result.output)["deployment_id"] == str(deployment_id)


def test_deploy_rejects_invalid_payload(tmp_path) -> None:
    path = tmp_path / "payload.json"
    path.write_text(json.dumps({"name": "missing-fields"}), encoding="utf-8")

    result = runner.invoke(app, ["deploy", str(path)])

    assert result.exit_code == 1
    payload = json.loads(result.output)
    assert payload["ok"] is False
    assert payload["error"]["code"] == "invalid_payload"


def test_run_now_with_fake_runner_executes_payload(tmp_path) -> None:
    payload_path = write_payload(tmp_path)

    result = runner.invoke(app, ["run-now", "--payload", str(payload_path), "--fake"])

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["ok"] is True
    assert payload["result"]["status"] == "succeeded"


def test_run_now_from_deployment(monkeypatch) -> None:
    flow_run_id = uuid4()

    monkeypatch.setattr(
        "agent_scheduler.cli.workflows._run_deployment_now",
        lambda ref: {"id": str(flow_run_id), "deployment_id": ref},
    )

    result = runner.invoke(app, ["run-now", "--deployment", str(uuid4())])

    assert result.exit_code == 0
    assert json.loads(result.output)["flow_run"]["id"] == str(flow_run_id)


def test_run_now_requires_one_source() -> None:
    result = runner.invoke(app, ["run-now"])

    assert result.exit_code == 1
    assert json.loads(result.output)["error"]["code"] == "invalid_request"


def test_schedule_management_commands(monkeypatch) -> None:
    deployment_id = uuid4()
    ref = str(deployment_id)

    monkeypatch.setattr(
        "agent_scheduler.cli.workflows._list_deployments",
        lambda limit, offset: [{"id": ref, "name": "daily"}],
    )
    monkeypatch.setattr(
        "agent_scheduler.cli.workflows._inspect_deployment",
        lambda deployment_ref: {"id": deployment_ref},
    )
    monkeypatch.setattr(
        "agent_scheduler.cli.workflows._pause_deployment",
        lambda deployment_ref: {"id": deployment_ref, "paused": True},
    )
    monkeypatch.setattr(
        "agent_scheduler.cli.workflows._resume_deployment",
        lambda deployment_ref: {"id": deployment_ref, "paused": False},
    )
    monkeypatch.setattr(
        "agent_scheduler.cli.workflows._delete_deployment",
        lambda deployment_ref: {"id": deployment_ref},
    )

    assert json.loads(runner.invoke(app, ["schedule", "list"]).output)["deployments"][0][
        "id"
    ] == ref
    assert json.loads(runner.invoke(app, ["schedule", "inspect", ref]).output)[
        "deployment"
    ]["id"] == ref
    assert json.loads(runner.invoke(app, ["schedule", "pause", ref]).output)[
        "deployment"
    ]["paused"] is True
    assert json.loads(runner.invoke(app, ["schedule", "resume", ref]).output)[
        "deployment"
    ]["paused"] is False
    assert json.loads(runner.invoke(app, ["schedule", "delete", ref]).output)[
        "deployment"
    ]["id"] == ref
