import pytest
from pydantic import ValidationError

from agent_scheduler.registry import (
    DuplicateWorkflowError,
    UnknownWorkflowError,
    WorkflowRegistry,
    default_registry,
)
from agent_scheduler.registry.workflows import RunSkillForAssetsWorkflow


def test_default_registry_contains_run_skill_for_assets() -> None:
    registry = default_registry()

    assert registry.names() == ["run_skill_for_assets"]


def test_unknown_workflow_is_rejected() -> None:
    registry = default_registry()

    with pytest.raises(UnknownWorkflowError) as exc_info:
        registry.get("unknown")

    assert exc_info.value.workflow_name == "unknown"


def test_duplicate_workflow_is_rejected() -> None:
    registry = WorkflowRegistry([RunSkillForAssetsWorkflow])

    with pytest.raises(DuplicateWorkflowError):
        registry.register(RunSkillForAssetsWorkflow)


def test_invalid_params_are_rejected_before_rendering() -> None:
    registry = default_registry()

    with pytest.raises(ValidationError):
        registry.render(
            "run_skill_for_assets",
            {"path_to_skill": "/skills/audit", "assets": []},
        )


def test_blank_asset_is_rejected() -> None:
    registry = default_registry()

    with pytest.raises(ValidationError):
        registry.render(
            "run_skill_for_assets",
            {"path_to_skill": "/skills/audit", "assets": ["asset-a", " "]},
        )


def test_unregistered_extra_params_are_rejected() -> None:
    registry = default_registry()

    with pytest.raises(ValidationError):
        registry.render(
            "run_skill_for_assets",
            {
                "path_to_skill": "/skills/audit",
                "assets": ["asset-a"],
                "command": "rm -rf /",
            },
        )


def test_disallowed_runner_is_rejected() -> None:
    registry = default_registry()

    with pytest.raises(ValueError, match="not allowed"):
        registry.render(
            "run_skill_for_assets",
            {"path_to_skill": "/skills/audit", "assets": ["asset-a"]},
            runner="other",  # type: ignore[arg-type]
        )


def test_registered_workflow_renders_deterministic_prompt() -> None:
    registry = default_registry()

    rendered = registry.render(
        "run_skill_for_assets",
        {
            "path_to_skill": "/skills/audit",
            "assets": ["asset-a", "asset-b"],
            "result_path": "/tmp/result.json",
        },
        runner="opencode",
    )

    assert rendered.name == "run_skill_for_assets"
    assert rendered.runner == "opencode"
    assert rendered.workspace == RunSkillForAssetsWorkflow.allowed_workspace
    assert rendered.policy.concurrency_limit == 1
    assert rendered.prompt == (
        "Run skill in /skills/audit for the following assets:\n"
        "- asset-a\n"
        "- asset-b\n\n"
        "Write the final result to: /tmp/result.json"
    )


def test_stock_market_close_summary_payload_for_gemi() -> None:
    skill_path = (
        "/home/inotives/.agent-knowledge/memory/3_intelligences/skills/trading/"
        "stock_market_close_summary"
    )

    rendered = default_registry().render(
        "run_skill_for_assets",
        {"path_to_skill": skill_path, "assets": ["GEMI"]},
        runner="codex",
    )

    assert rendered.prompt == (
        f"Run skill in {skill_path} for the following assets:\n"
        "- GEMI"
    )
