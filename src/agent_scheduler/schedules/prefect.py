from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from prefect.schedules import Cron, RRule, Schedule, validate_cron_string

from agent_scheduler.schedules.types import (
    CronScheduleSpec,
    OneShotScheduleSpec,
    ScheduleSpec,
)


def build_prefect_schedule(spec: ScheduleSpec) -> Schedule:
    if isinstance(spec, CronScheduleSpec):
        validate_cron_string(spec.cron)
        return Cron(spec.cron, timezone=spec.timezone)

    if isinstance(spec, OneShotScheduleSpec):
        return RRule(_one_shot_rrule(spec.run_at, spec.timezone), timezone=spec.timezone)

    raise TypeError(f"unsupported schedule spec: {type(spec).__name__}")


def _one_shot_rrule(run_at: datetime, timezone: str) -> str:
    zone = ZoneInfo(timezone)
    if run_at.tzinfo is None:
        local_run_at = run_at
    else:
        local_run_at = run_at.astimezone(zone).replace(tzinfo=None)
    start = local_run_at.strftime("%Y%m%dT%H%M%S")
    return f"DTSTART:{start}\nRRULE:FREQ=DAILY;COUNT=1"
