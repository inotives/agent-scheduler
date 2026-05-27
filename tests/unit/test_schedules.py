from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from agent_scheduler.schedules import (
    CronScheduleSpec,
    OneShotScheduleSpec,
    WorkflowDeploymentSpec,
    build_prefect_schedule,
)


def test_cron_schedule_requires_valid_timezone() -> None:
    with pytest.raises(ValidationError):
        CronScheduleSpec(cron="0 16 * * *", timezone="Not/AZone")


def test_builds_prefect_cron_schedule() -> None:
    schedule = build_prefect_schedule(
        CronScheduleSpec(cron="0 16 * * *", timezone="Asia/Jakarta")
    )

    assert schedule.cron == "0 16 * * *"
    assert schedule.timezone == "Asia/Jakarta"


def test_invalid_cron_is_rejected() -> None:
    with pytest.raises(ValueError):
        build_prefect_schedule(CronScheduleSpec(cron="bad", timezone="Asia/Jakarta"))


def test_builds_one_shot_schedule_as_single_rrule() -> None:
    schedule = build_prefect_schedule(
        OneShotScheduleSpec(
            run_at=datetime(2026, 5, 26, 16, 0, tzinfo=timezone.utc),
            timezone="Asia/Jakarta",
        )
    )

    assert "COUNT=1" in schedule.rrule
    assert "DTSTART:20260526T230000" in schedule.rrule
    assert schedule.timezone == "Asia/Jakarta"


def test_deployment_spec_rejects_blank_name() -> None:
    with pytest.raises(ValidationError):
        WorkflowDeploymentSpec(
            name=" ",
            workflow_name="run_skill_for_assets",
            params={"path_to_skill": "/skills/audit", "assets": ["GEMI"]},
            schedule={"type": "cron", "cron": "0 16 * * *", "timezone": "Asia/Jakarta"},
        )


def test_deployment_spec_accepts_public_task_alias() -> None:
    spec = WorkflowDeploymentSpec.model_validate(
        {
            "name": "daily-stock-market-close-summary",
            "task": "run_skill_for_assets",
            "params": {"path_to_skill": "/skills/audit", "assets": ["GEMI"]},
            "schedule": {"type": "cron", "cron": "0 16 * * *", "timezone": "Asia/Jakarta"},
        }
    )

    assert spec.workflow_name == "run_skill_for_assets"
