from __future__ import annotations

import string
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from agent_scheduler.registry.types import RegisteredWorkflow, WorkflowPolicy


PromptVariable = str | int | float | bool | list[str] | None


class RunPromptParams(BaseModel):
    model_config = ConfigDict(extra="forbid")

    prompt: str = Field(min_length=1)
    variables: dict[str, PromptVariable] = Field(default_factory=dict)
    completion_signal_path: Path | None = None

    @field_validator("prompt")
    @classmethod
    def prompt_must_not_be_blank(cls, prompt: str) -> str:
        if not prompt.strip():
            raise ValueError("prompt must not be blank")
        return prompt

    @field_validator("variables")
    @classmethod
    def variables_must_be_renderable(
        cls, variables: dict[str, PromptVariable]
    ) -> dict[str, PromptVariable]:
        formatter = string.Formatter()
        for name, value in variables.items():
            if not name.isidentifier():
                raise ValueError(f"variable name must be a valid identifier: {name}")
            if isinstance(value, list) and any(not item.strip() for item in value):
                raise ValueError(f"variable list must not contain blank values: {name}")
            if isinstance(value, str) and not value.strip():
                raise ValueError(f"variable value must not be blank: {name}")
            for _, field_name, _, _ in formatter.parse(name):
                if field_name is not None:
                    raise ValueError(f"variable name must not contain format fields: {name}")
        return variables

    @field_validator("completion_signal_path", mode="before")
    @classmethod
    def completion_signal_path_must_not_be_blank(cls, path: Any) -> Any:
        if path is not None and not str(path).strip():
            raise ValueError("completion_signal_path must not be blank")
        return path


class RunPromptWorkflow(RegisteredWorkflow):
    name = "run_prompt"
    params_model = RunPromptParams
    allowed_workspace = Path.cwd()
    allowed_runners = ("claude", "codex", "opencode")
    default_runner = "opencode"
    policy = WorkflowPolicy(
        retries=0,
        retry_delay_seconds=60,
        timeout_seconds=3600,
        concurrency_limit=1,
        allow_cli_policy_overrides=False,
    )

    @classmethod
    def render_prompt(cls, params: BaseModel) -> str:
        workflow_params = cls._coerce_params(params)
        variables = {
            name: _render_variable(value)
            for name, value in workflow_params.variables.items()
        }
        if workflow_params.completion_signal_path is not None:
            variables.setdefault(
                "completion_signal_path",
                str(workflow_params.completion_signal_path),
            )
        try:
            return workflow_params.prompt.format(**variables)
        except KeyError as exc:
            missing_name = str(exc).strip("'")
            raise ValueError(f"missing prompt variable: {missing_name}") from exc
        except (IndexError, ValueError) as exc:
            raise ValueError(f"invalid prompt template: {exc}") from exc

    @staticmethod
    def _coerce_params(params: BaseModel) -> RunPromptParams:
        if isinstance(params, RunPromptParams):
            return params
        return RunPromptParams.model_validate(params.model_dump())


def _render_variable(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        return ", ".join(value)
    return str(value)
