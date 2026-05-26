from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import ClassVar, Literal

from pydantic import BaseModel, ConfigDict, Field


RunnerType = Literal["codex", "opencode"]


class WorkflowPolicy(BaseModel):
    retries: int = Field(default=0, ge=0)
    retry_delay_seconds: int = Field(default=60, ge=0)
    timeout_seconds: int = Field(default=3600, ge=1)
    concurrency_limit: int = Field(default=1, ge=1)
    allow_cli_policy_overrides: bool = False


class RenderedWorkflow(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: str
    params: BaseModel
    workspace: Path
    runner: RunnerType
    prompt: str
    policy: WorkflowPolicy


class RegisteredWorkflow(ABC):
    name: ClassVar[str]
    params_model: ClassVar[type[BaseModel]]
    allowed_workspace: ClassVar[Path]
    allowed_runners: ClassVar[tuple[RunnerType, ...]]
    default_runner: ClassVar[RunnerType]
    policy: ClassVar[WorkflowPolicy] = WorkflowPolicy()

    @classmethod
    def validate_params(cls, raw_params: dict) -> BaseModel:
        return cls.params_model.model_validate(raw_params)

    @classmethod
    def render(
        cls,
        raw_params: dict,
        runner: RunnerType | None = None,
    ) -> RenderedWorkflow:
        selected_runner = runner or cls.default_runner
        if selected_runner not in cls.allowed_runners:
            allowed = ", ".join(cls.allowed_runners)
            raise ValueError(
                f"Runner '{selected_runner}' is not allowed for {cls.name}; allowed: {allowed}"
            )

        params = cls.validate_params(raw_params)
        return RenderedWorkflow(
            name=cls.name,
            params=params,
            workspace=cls.allowed_workspace,
            runner=selected_runner,
            prompt=cls.render_prompt(params),
            policy=cls.policy,
        )

    @classmethod
    @abstractmethod
    def render_prompt(cls, params: BaseModel) -> str:
        """Render a deterministic prompt for the validated workflow params."""
