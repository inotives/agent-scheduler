import subprocess
from pathlib import Path

import pytest

from agent_scheduler.runners import (
    CodexRunnerAdapter,
    FakeRunnerAdapter,
    OpenCodeRunnerAdapter,
    RunnerContext,
    RunnerMetadata,
    UnknownRunnerError,
    runner_for,
)


def runner_context(tmp_path: Path) -> RunnerContext:
    return RunnerContext(
        task_name="run_skill_for_assets",
        params={"path_to_skill": "/skills/audit", "assets": ["GEMI"]},
        workspace=tmp_path,
        runner="codex",
        prompt="Run skill in /skills/audit for the following assets:\n- GEMI",
        metadata=RunnerMetadata(flow_run_id="flow-run-1", attempt=2),
    )


def test_runner_context_serializes_to_json(tmp_path) -> None:
    context = runner_context(tmp_path)

    payload = context.to_json_payload()

    assert '"task_name":"run_skill_for_assets"' in payload
    assert '"flow_run_id":"flow-run-1"' in payload
    assert '"attempt":2' in payload


def test_fake_runner_returns_context_payload(tmp_path) -> None:
    context = runner_context(tmp_path)

    result = FakeRunnerAdapter().run(context, timeout_seconds=1)

    assert result.succeeded is True
    assert result.status == "succeeded"
    assert result.exit_code == 0
    assert '"task_name":"run_skill_for_assets"' in result.stdout


def test_fake_runner_can_fail(tmp_path) -> None:
    context = runner_context(tmp_path)

    result = FakeRunnerAdapter(exit_code=2, stderr="failed").run(context, timeout_seconds=1)

    assert result.succeeded is False
    assert result.status == "failed"
    assert result.exit_code == 2
    assert result.stderr == "failed"


def test_codex_argv_is_isolated_from_prompt() -> None:
    adapter = CodexRunnerAdapter()
    context = RunnerContext(
        task_name="task",
        params={},
        workspace=Path.cwd(),
        runner="codex",
        prompt="secret prompt",
    )

    assert adapter.build_argv(context) == ["codex", "exec", "--full-auto", "-"]


def test_opencode_argv_uses_message_argument() -> None:
    adapter = OpenCodeRunnerAdapter()
    context = RunnerContext(
        task_name="task",
        params={},
        workspace=Path.cwd(),
        runner="opencode",
        prompt="Run a task",
    )

    assert adapter.build_argv(context) == ["opencode", "run", "Run a task"]


def test_subprocess_runner_sends_prompt_on_stdin(monkeypatch, tmp_path) -> None:
    context = runner_context(tmp_path)
    calls = []

    def fake_run(*args, **kwargs):
        calls.append((args, kwargs))
        return subprocess.CompletedProcess(args=args[0], returncode=0, stdout="ok", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)

    result = CodexRunnerAdapter().run(context, timeout_seconds=30)

    assert result.status == "succeeded"
    assert result.exit_code == 0
    assert result.stdout == "ok"
    assert calls[0][0] == (["codex", "exec", "--full-auto", "-"],)
    assert calls[0][1]["input"] == context.prompt
    assert calls[0][1]["cwd"] == tmp_path
    assert calls[0][1]["timeout"] == 30


def test_subprocess_runner_maps_nonzero_exit_to_failure(monkeypatch, tmp_path) -> None:
    context = runner_context(tmp_path)

    def fake_run(*args, **kwargs):
        return subprocess.CompletedProcess(args=args[0], returncode=7, stdout="", stderr="nope")

    monkeypatch.setattr(subprocess, "run", fake_run)

    result = CodexRunnerAdapter().run(context, timeout_seconds=30)

    assert result.succeeded is False
    assert result.status == "failed"
    assert result.exit_code == 7
    assert result.stderr == "nope"


def test_subprocess_runner_maps_timeout(monkeypatch, tmp_path) -> None:
    context = runner_context(tmp_path)

    def fake_run(*args, **kwargs):
        raise subprocess.TimeoutExpired(args[0], timeout=1, output="partial", stderr="late")

    monkeypatch.setattr(subprocess, "run", fake_run)

    result = CodexRunnerAdapter().run(context, timeout_seconds=1)

    assert result.succeeded is False
    assert result.status == "timed_out"
    assert result.exit_code is None
    assert result.stdout == "partial"
    assert result.stderr == "late"
    assert result.timed_out is True


def test_runner_factory_returns_known_adapters() -> None:
    assert isinstance(runner_for("codex"), CodexRunnerAdapter)
    assert isinstance(runner_for("opencode"), OpenCodeRunnerAdapter)


def test_runner_factory_rejects_unknown_runner() -> None:
    with pytest.raises(UnknownRunnerError):
        runner_for("other")  # type: ignore[arg-type]
