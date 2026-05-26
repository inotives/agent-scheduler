from __future__ import annotations

from datetime import datetime
from typing import Literal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from agent_scheduler.registry import RunnerType


class CronScheduleSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["cron"] = "cron"
    cron: str
    timezone: str

    @field_validator("timezone")
    @classmethod
    def timezone_must_exist(cls, timezone: str) -> str:
        try:
            ZoneInfo(timezone)
        except ZoneInfoNotFoundError as exc:
            raise ValueError(f"unknown timezone: {timezone}") from exc
        return timezone


class OneShotScheduleSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["once"] = "once"
    run_at: datetime
    timezone: str

    @field_validator("timezone")
    @classmethod
    def timezone_must_exist(cls, timezone: str) -> str:
        try:
            ZoneInfo(timezone)
        except ZoneInfoNotFoundError as exc:
            raise ValueError(f"unknown timezone: {timezone}") from exc
        return timezone

    @model_validator(mode="after")
    def run_at_must_be_set(self) -> OneShotScheduleSpec:
        if self.run_at is None:
            raise ValueError("run_at is required")
        return self


ScheduleSpec = CronScheduleSpec | OneShotScheduleSpec


class WorkflowDeploymentSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)
    workflow_name: str = Field(min_length=1)
    params: dict
    runner: RunnerType | None = None
    schedule: ScheduleSpec
    work_pool_name: str = Field(default="agent-scheduler", min_length=1)
    work_queue_name: str | None = None
    paused: bool = False

    @field_validator("name", "workflow_name", "work_pool_name")
    @classmethod
    def strings_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("value must not be blank")
        return value
