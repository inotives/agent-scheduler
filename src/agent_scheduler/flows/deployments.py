from __future__ import annotations

from uuid import UUID

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
    schedule = build_prefect_schedule(spec.schedule)
    deployment_id = run_agent_workflow.deploy(
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
        build=False,
        push=False,
        print_next_steps=False,
    )
    return deployment_id
