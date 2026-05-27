from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from agent_scheduler.registry import RunnerType


RunnerStatus = Literal["succeeded", "failed", "timed_out"]


class RunnerMetadata(BaseModel):
    flow_run_id: str | None = None
    schedule_id: str | None = None
    deployment_id: str | None = None
    attempt: int = Field(default=1, ge=1)


class RunnerContext(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    task_name: str
    params: dict[str, Any]
    workspace: Path
    runner: RunnerType
    prompt: str
    metadata: RunnerMetadata = Field(default_factory=RunnerMetadata)

    def to_json_payload(self) -> str:
        return self.model_dump_json()


class RunnerResult(BaseModel):
    runner: RunnerType | Literal["fake"]
    status: RunnerStatus
    exit_code: int | None
    stdout: str = ""
    stderr: str = ""
    timed_out: bool = False

    @property
    def succeeded(self) -> bool:
        return self.status == "succeeded"

