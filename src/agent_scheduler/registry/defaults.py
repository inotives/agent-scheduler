from __future__ import annotations

from agent_scheduler.registry.store import WorkflowRegistry
from agent_scheduler.registry.workflows import (
    AgentSmokeWorkflow,
    RunPromptWorkflow,
    RunSkillForAssetsWorkflow,
)


def default_registry() -> WorkflowRegistry:
    return WorkflowRegistry(
        [RunPromptWorkflow, RunSkillForAssetsWorkflow, AgentSmokeWorkflow]
    )
