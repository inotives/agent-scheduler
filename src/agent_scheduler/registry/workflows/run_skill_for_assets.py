from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from agent_scheduler.registry.types import RegisteredWorkflow, WorkflowPolicy


class RunSkillForAssetsParams(BaseModel):
    model_config = ConfigDict(extra="forbid")

    path_to_skill: Path
    assets: list[str] = Field(min_length=1)
    result_path: Path | None = None

    @field_validator("assets")
    @classmethod
    def assets_must_not_be_blank(cls, assets: list[str]) -> list[str]:
        blank_assets = [asset for asset in assets if not asset.strip()]
        if blank_assets:
            raise ValueError("assets must not contain blank values")
        return assets

    @field_validator("path_to_skill", "result_path", mode="before")
    @classmethod
    def paths_must_not_be_blank(cls, path: Any) -> Any:
        if path is not None and not str(path).strip():
            raise ValueError("path must not be blank")
        return path


class RunSkillForAssetsWorkflow(RegisteredWorkflow):
    name = "run_skill_for_assets"
    params_model = RunSkillForAssetsParams
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
        assets = "\n".join(f"- {asset}" for asset in workflow_params.assets)

        prompt = (
            f"Run skill in {workflow_params.path_to_skill} for the following assets:\n"
            f"{assets}"
        )
        if workflow_params.result_path is not None:
            prompt = f"{prompt}\n\nWrite the final result to: {workflow_params.result_path}"
        return prompt

    @staticmethod
    def _coerce_params(params: BaseModel) -> RunSkillForAssetsParams:
        if isinstance(params, RunSkillForAssetsParams):
            return params
        return RunSkillForAssetsParams.model_validate(params.model_dump())
