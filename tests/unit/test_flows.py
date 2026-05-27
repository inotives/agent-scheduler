from pathlib import Path

import pytest

from agent_scheduler.flows import execute_registered_workflow
from agent_scheduler.runners import FakeRunnerAdapter, RunnerAdapter, RunnerContext, RunnerResult


def test_execute_registered_workflow_with_fake_runner() -> None:
    result = execute_registered_workflow(
        "run_skill_for_assets",
        {"path_to_skill": "/skills/audit", "assets": ["GEMI"]},
        runner="codex",
        adapter=FakeRunnerAdapter(),
    )

    assert result.succeeded is True
    assert result.exit_code == 0
    assert '"task_name":"run_skill_for_assets"' in result.stdout
    assert str(Path.cwd()) in result.stdout


def test_execute_registered_workflow_propagates_runner_failure() -> None:
    with pytest.raises(RuntimeError, match="failed"):
        execute_registered_workflow(
            "run_skill_for_assets",
            {"path_to_skill": "/skills/audit", "assets": ["GEMI"]},
            runner="codex",
            adapter=FakeRunnerAdapter(exit_code=9, stderr="nope"),
        )


def test_execute_registered_workflow_verifies_completion_signal(tmp_path) -> None:
    signal_path = tmp_path / "report.done.json"

    result = execute_registered_workflow(
        "run_prompt",
        {
            "prompt": "Run report and write {completion_signal_path}.",
            "completion_signal_path": signal_path,
        },
        adapter=SignalWritingAdapter(signal_path),
    )

    assert result.succeeded is True


def test_execute_registered_workflow_fails_when_completion_signal_is_missing(
    tmp_path,
) -> None:
    signal_path = tmp_path / "missing.done.json"

    with pytest.raises(RuntimeError, match="completion signal was not written"):
        execute_registered_workflow(
            "run_prompt",
            {
                "prompt": "Run report and write {completion_signal_path}.",
                "completion_signal_path": signal_path,
            },
            adapter=NoSignalAdapter(),
        )


class SignalWritingAdapter(RunnerAdapter):
    def __init__(self, signal_path: Path) -> None:
        self.signal_path = signal_path

    def run(self, context: RunnerContext, timeout_seconds: int) -> RunnerResult:
        self.signal_path.write_text('{"status":"completed"}', encoding="utf-8")
        return RunnerResult(
            runner=context.runner,
            status="succeeded",
            exit_code=0,
            stdout="done",
        )


class NoSignalAdapter(RunnerAdapter):
    def run(self, context: RunnerContext, timeout_seconds: int) -> RunnerResult:
        return RunnerResult(
            runner=context.runner,
            status="succeeded",
            exit_code=0,
            stdout="done",
        )
