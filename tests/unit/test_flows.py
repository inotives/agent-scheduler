from pathlib import Path

import pytest

from agent_scheduler.flows import execute_registered_workflow
from agent_scheduler.runners import FakeRunnerAdapter


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
