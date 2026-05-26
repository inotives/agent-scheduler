from __future__ import annotations

from agent_scheduler.registry.store import WorkflowRegistry
from agent_scheduler.registry.workflows import RunSkillForAssetsWorkflow


def default_registry() -> WorkflowRegistry:
    return WorkflowRegistry([RunSkillForAssetsWorkflow])

