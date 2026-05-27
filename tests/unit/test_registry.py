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

    assert registry.names() == ["agent_smoke", "run_prompt", "run_skill_for_assets"]


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


def test_registered_workflow_defaults_to_opencode() -> None:
    rendered = default_registry().render(
        "run_prompt",
        {"prompt": "Say hello."},
    )

    assert rendered.runner == "opencode"


def test_run_prompt_allows_claude_runner() -> None:
    rendered = default_registry().render(
        "run_prompt",
        {"prompt": "Say hello."},
        runner="claude",
    )

    assert rendered.runner == "claude"
    assert rendered.prompt == "Say hello."


def test_run_prompt_renders_text_with_variables() -> None:
    rendered = default_registry().render(
        "run_prompt",
        {
            "prompt": "Run {skill_path} for {assets} on {market_close_date}.",
            "variables": {
                "skill_path": "/skills/market_close_summary",
                "assets": ["GEMI", "PLTR"],
                "market_close_date": "2026-05-26",
            },
        },
    )

    assert rendered.runner == "opencode"
    assert rendered.prompt == (
        "Run /skills/market_close_summary for GEMI, PLTR on 2026-05-26."
    )


def test_run_prompt_renders_completion_signal_path_variable() -> None:
    rendered = default_registry().render(
        "run_prompt",
        {
            "prompt": "Run report, then write signal to {completion_signal_path}.",
            "completion_signal_path": "outputs/report.done.json",
        },
    )

    assert rendered.prompt == "Run report, then write signal to outputs/report.done.json."


def test_run_prompt_prefers_top_level_completion_signal_path() -> None:
    rendered = default_registry().render(
        "run_prompt",
        {
            "prompt": "Run report, then write signal to {completion_signal_path}.",
            "variables": {"completion_signal_path": "outputs/old.done.json"},
            "completion_signal_path": "outputs/new.done.json",
        },
    )

    assert rendered.prompt == "Run report, then write signal to outputs/new.done.json."


def test_run_prompt_rejects_missing_variables() -> None:
    registry = default_registry()

    with pytest.raises(ValueError, match="missing prompt variable: market_close_date"):
        registry.render(
            "run_prompt",
            {
                "prompt": "Run summary for {assets} on {market_close_date}.",
                "variables": {"assets": ["GEMI"]},
            },
        )


def test_run_prompt_rejects_invalid_variable_names() -> None:
    registry = default_registry()

    with pytest.raises(ValidationError):
        registry.render(
            "run_prompt",
            {
                "prompt": "Run summary for {assets}.",
                "variables": {"asset-list": ["GEMI"]},
            },
        )


def test_stock_market_close_summary_payload_for_gemi_and_pltr() -> None:
    skill_path = "examples/flows/market_close_summary"

    rendered = default_registry().render(
        "run_prompt",
        {
            "prompt": (
                "Run skill in {skill_path} for the following assets: {assets}.\n\n"
                "Market close date: {market_close_date}."
            ),
            "variables": {
                "skill_path": skill_path,
                "assets": ["GEMI", "PLTR"],
                "assets_json": '["GEMI","PLTR"]',
                "market_close_date": "2026-05-26",
            },
        },
    )

    assert rendered.runner == "opencode"
    assert rendered.prompt == (
        f"Run skill in {skill_path} for the following assets: GEMI, PLTR.\n\n"
        "Market close date: 2026-05-26."
    )


def test_agent_smoke_defaults_to_opencode() -> None:
    rendered = default_registry().render("agent_smoke", {"message": "Say hello and exit."})

    assert rendered.runner == "opencode"
    assert rendered.prompt == "Say hello and exit."
