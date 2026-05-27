"""Schedule parsing and lifecycle helpers."""
"""Schedule specs and Prefect schedule builders."""

from agent_scheduler.schedules.types import (
    CronScheduleSpec,
    OneShotScheduleSpec,
    ScheduleSpec,
    WorkflowDeploymentSpec,
)

__all__ = [
    "CronScheduleSpec",
    "OneShotScheduleSpec",
    "ScheduleSpec",
    "WorkflowDeploymentSpec",
    "build_prefect_schedule",
]


def __getattr__(name: str):
    if name == "build_prefect_schedule":
        from agent_scheduler.schedules.prefect import build_prefect_schedule

        return build_prefect_schedule
    raise AttributeError(name)
