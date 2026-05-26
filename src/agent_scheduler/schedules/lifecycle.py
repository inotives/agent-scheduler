from __future__ import annotations

from typing import Any
from uuid import UUID

from prefect.client.orchestration import get_client


AGENT_SCHEDULER_FLOW_NAME = "agent-scheduler-run-workflow"


def list_deployments(limit: int = 100, offset: int = 0) -> list[dict[str, Any]]:
    with get_client(sync_client=True) as client:
        deployments = client.read_deployments(limit=limit, offset=offset)
    return [_deployment_summary(deployment) for deployment in deployments]


def inspect_deployment(ref: str) -> dict[str, Any]:
    return _deployment_summary(_read_deployment(ref))


def pause_deployment(ref: str) -> dict[str, Any]:
    deployment = _read_deployment(ref)
    with get_client(sync_client=True) as client:
        client.pause_deployment(getattr(deployment, "id"))
    summary = _deployment_summary(deployment)
    summary["paused"] = True
    return summary


def resume_deployment(ref: str) -> dict[str, Any]:
    deployment = _read_deployment(ref)
    with get_client(sync_client=True) as client:
        client.resume_deployment(getattr(deployment, "id"))
    summary = _deployment_summary(deployment)
    summary["paused"] = False
    return summary


def delete_deployment(ref: str) -> dict[str, Any]:
    deployment = _read_deployment(ref)
    with get_client(sync_client=True) as client:
        client.delete_deployment(getattr(deployment, "id"))
    return _deployment_summary(deployment)


def run_deployment_now(ref: str, parameters: dict[str, Any] | None = None) -> dict[str, Any]:
    deployment = _read_deployment(ref)
    with get_client(sync_client=True) as client:
        flow_run = client.create_flow_run_from_deployment(
            getattr(deployment, "id"),
            parameters=parameters,
        )
    return _flow_run_summary(flow_run)


def _read_deployment(ref: str):
    with get_client(sync_client=True) as client:
        if "/" in ref:
            return client.read_deployment_by_name(ref)
        return client.read_deployment(UUID(ref))


def _deployment_summary(deployment) -> dict[str, Any]:
    return {
        "id": str(getattr(deployment, "id")),
        "name": getattr(deployment, "name", None),
        "flow_id": _optional_str(getattr(deployment, "flow_id", None)),
        "paused": getattr(deployment, "paused", None),
        "work_pool_name": getattr(deployment, "work_pool_name", None),
        "work_queue_name": getattr(deployment, "work_queue_name", None),
        "parameters": getattr(deployment, "parameters", None) or {},
        "tags": getattr(deployment, "tags", None) or [],
    }


def _flow_run_summary(flow_run) -> dict[str, Any]:
    state = getattr(flow_run, "state", None)
    return {
        "id": str(getattr(flow_run, "id")),
        "name": getattr(flow_run, "name", None),
        "deployment_id": _optional_str(getattr(flow_run, "deployment_id", None)),
        "state_type": str(getattr(state, "type", "")) if state else None,
        "state_name": getattr(state, "name", None) if state else None,
    }


def _optional_str(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)
