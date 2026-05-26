from __future__ import annotations

from agent_scheduler.registry.errors import DuplicateWorkflowError, UnknownWorkflowError
from agent_scheduler.registry.types import RegisteredWorkflow, RenderedWorkflow, RunnerType


class WorkflowRegistry:
    def __init__(self, workflows: list[type[RegisteredWorkflow]] | None = None) -> None:
        self._workflows: dict[str, type[RegisteredWorkflow]] = {}
        for workflow in workflows or []:
            self.register(workflow)

    def register(self, workflow: type[RegisteredWorkflow]) -> None:
        if workflow.name in self._workflows:
            raise DuplicateWorkflowError(workflow.name)
        self._workflows[workflow.name] = workflow

    def names(self) -> list[str]:
        return sorted(self._workflows)

    def get(self, workflow_name: str) -> type[RegisteredWorkflow]:
        try:
            return self._workflows[workflow_name]
        except KeyError as exc:
            raise UnknownWorkflowError(workflow_name) from exc

    def render(
        self,
        workflow_name: str,
        raw_params: dict,
        runner: RunnerType | None = None,
    ) -> RenderedWorkflow:
        return self.get(workflow_name).render(raw_params, runner=runner)

