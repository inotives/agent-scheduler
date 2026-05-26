from __future__ import annotations

from prefect.client.schemas.objects import ConcurrencyLimitConfig, ConcurrencyLimitStrategy
from prefect.client.orchestration import get_client

from agent_scheduler.registry import RenderedWorkflow

GLOBAL_CONCURRENCY_KEY = "agent-scheduler:global"


def deployment_concurrency_limit(rendered: RenderedWorkflow) -> ConcurrencyLimitConfig:
    return ConcurrencyLimitConfig(
        limit=rendered.policy.concurrency_limit,
        collision_strategy=ConcurrencyLimitStrategy.ENQUEUE,
    )


def concurrency_key(rendered: RenderedWorkflow) -> str:
    workspace = str(rendered.workspace.resolve())
    return f"{rendered.name}:{workspace}"


def runtime_concurrency_keys(rendered: RenderedWorkflow) -> list[str]:
    return [GLOBAL_CONCURRENCY_KEY, concurrency_key(rendered)]


def upsert_runtime_concurrency_limits(
    rendered: RenderedWorkflow,
    global_limit: int = 2,
) -> None:
    with get_client(sync_client=True) as client:
        client.upsert_global_concurrency_limit_by_name(
            GLOBAL_CONCURRENCY_KEY,
            global_limit,
        )
        client.upsert_global_concurrency_limit_by_name(
            concurrency_key(rendered),
            rendered.policy.concurrency_limit,
        )
