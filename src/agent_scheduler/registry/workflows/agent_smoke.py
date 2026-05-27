from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, field_validator

from agent_scheduler.registry.types import RegisteredWorkflow, WorkflowPolicy


class AgentSmokeParams(BaseModel):
    model_config = ConfigDict(extra="forbid")

    message: str = Field(default="Say hello and exit.", min_length=1)

    @field_validator("message")
    @classmethod
    def message_must_not_be_blank(cls, message: str) -> str:
        if not message.strip():
            raise ValueError("message must not be blank")
        return message


class AgentSmokeWorkflow(RegisteredWorkflow):
    name = "agent_smoke"
    params_model = AgentSmokeParams
    allowed_workspace = Path.cwd()
    allowed_runners = ("claude", "codex", "opencode")
    default_runner = "opencode"
    policy = WorkflowPolicy(
        retries=0,
        retry_delay_seconds=0,
        timeout_seconds=120,
        concurrency_limit=1,
        allow_cli_policy_overrides=False,
    )

    @classmethod
    def render_prompt(cls, params: BaseModel) -> str:
        workflow_params = cls._coerce_params(params)
        return workflow_params.message

    @staticmethod
    def _coerce_params(params: BaseModel) -> AgentSmokeParams:
        if isinstance(params, AgentSmokeParams):
            return params
        return AgentSmokeParams.model_validate(params.model_dump())
