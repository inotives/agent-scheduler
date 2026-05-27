from __future__ import annotations

from pathlib import Path
from uuid import UUID

from prefect.client.orchestration import get_client
from prefect.client.schemas.actions import WorkPoolCreate

from agent_scheduler.concurrency import (
    deployment_concurrency_limit,
    upsert_runtime_concurrency_limits,
)
from agent_scheduler.flows.agent_workflow import run_agent_workflow
from agent_scheduler.registry import default_registry
from agent_scheduler.schedules import WorkflowDeploymentSpec, build_prefect_schedule


def deploy_workflow(spec: WorkflowDeploymentSpec, global_concurrency_limit: int = 2) -> UUID:
    rendered = default_registry().render(spec.workflow_name, spec.params, runner=spec.runner)
    upsert_runtime_concurrency_limits(rendered, global_limit=global_concurrency_limit)
    ensure_work_pool(spec.work_pool_name)
    schedule = build_prefect_schedule(spec.schedule)
    flow = run_agent_workflow.with_options(
        retries=rendered.policy.retries,
        retry_delay_seconds=rendered.policy.retry_delay_seconds,
        timeout_seconds=rendered.policy.timeout_seconds + 30,
    )
    deployment = flow.to_deployment(
        name=spec.name,
        work_pool_name=spec.work_pool_name,
        work_queue_name=spec.work_queue_name,
        schedule=schedule,
        paused=spec.paused,
        parameters={
            "workflow_name": spec.workflow_name,
            "params": rendered.params.model_dump(mode="json"),
            "runner": rendered.runner,
        },
        concurrency_limit=deployment_concurrency_limit(rendered),
        job_variables={"working_dir": str(Path.cwd())},
    )
    deployment_id = deployment.apply(work_pool_name=spec.work_pool_name)
    return deployment_id


def ensure_work_pool(work_pool_name: str, work_pool_type: str = "process") -> None:
    with get_client(sync_client=True) as client:
        client.create_work_pool(
            WorkPoolCreate(name=work_pool_name, type=work_pool_type),
            overwrite=True,
        )
