from __future__ import annotations

from pathlib import Path
from typing import Annotated, Any

import typer
from pydantic import ValidationError

from agent_scheduler.cli.json_output import (
    echo_error,
    echo_json,
    read_json_file,
    validation_details,
)
from agent_scheduler.config.settings import apply_prefect_environment, load_settings
from agent_scheduler.schedules.types import WorkflowDeploymentSpec


schedule_app = typer.Typer(help="Create and manage workflow schedules.")


def deploy_from_payload(payload_path: Path, env: str | None = None) -> None:
    try:
        payload = read_json_file(payload_path)
        spec = WorkflowDeploymentSpec.model_validate(payload)
        settings = _apply_runtime_env(env)
        deployment_id = _deploy_workflow(
            spec,
            global_concurrency_limit=settings.agent_scheduler_global_concurrency,
        )
    except ValidationError as exc:
        echo_error("invalid_payload", "Payload validation failed.", validation_details(exc))
    except Exception as exc:
        echo_error("deploy_failed", str(exc))

    echo_json({"ok": True, "deployment_id": str(deployment_id), "name": spec.name})


@schedule_app.command("create")
def schedule_create(
    payload_path: Annotated[Path, typer.Argument(help="Path to schedule JSON payload.")],
    env: Annotated[str | None, typer.Option("--env", help="Environment name.")] = None,
) -> None:
    """Create or update a scheduled workflow deployment."""
    deploy_from_payload(payload_path, env=env)


@schedule_app.command("update")
def schedule_update(
    payload_path: Annotated[Path, typer.Argument(help="Path to schedule JSON payload.")],
    env: Annotated[str | None, typer.Option("--env", help="Environment name.")] = None,
) -> None:
    """Update a scheduled workflow deployment by name."""
    deploy_from_payload(payload_path, env=env)


@schedule_app.command("list")
def schedule_list(
    limit: Annotated[int, typer.Option("--limit", min=1, max=500)] = 100,
    offset: Annotated[int, typer.Option("--offset", min=0)] = 0,
    env: Annotated[str | None, typer.Option("--env", help="Environment name.")] = None,
) -> None:
    try:
        _apply_runtime_env(env)
        deployments = _list_deployments(limit=limit, offset=offset)
    except Exception as exc:
        echo_error("list_failed", str(exc))
    echo_json({"ok": True, "deployments": deployments})


@schedule_app.command("inspect")
def schedule_inspect(
    ref: Annotated[str, typer.Argument(help="Deployment UUID or flow/deployment name.")],
    env: Annotated[str | None, typer.Option("--env", help="Environment name.")] = None,
) -> None:
    try:
        _apply_runtime_env(env)
        deployment = _inspect_deployment(ref)
    except Exception as exc:
        echo_error("inspect_failed", str(exc))
    echo_json({"ok": True, "deployment": deployment})


@schedule_app.command("pause")
def schedule_pause(
    ref: Annotated[str, typer.Argument(help="Deployment UUID or flow/deployment name.")],
    env: Annotated[str | None, typer.Option("--env", help="Environment name.")] = None,
) -> None:
    try:
        _apply_runtime_env(env)
        deployment = _pause_deployment(ref)
    except Exception as exc:
        echo_error("pause_failed", str(exc))
    echo_json({"ok": True, "deployment": deployment})


@schedule_app.command("resume")
def schedule_resume(
    ref: Annotated[str, typer.Argument(help="Deployment UUID or flow/deployment name.")],
    env: Annotated[str | None, typer.Option("--env", help="Environment name.")] = None,
) -> None:
    try:
        _apply_runtime_env(env)
        deployment = _resume_deployment(ref)
    except Exception as exc:
        echo_error("resume_failed", str(exc))
    echo_json({"ok": True, "deployment": deployment})


@schedule_app.command("delete")
def schedule_delete(
    ref: Annotated[str, typer.Argument(help="Deployment UUID or flow/deployment name.")],
    env: Annotated[str | None, typer.Option("--env", help="Environment name.")] = None,
) -> None:
    try:
        _apply_runtime_env(env)
        deployment = _delete_deployment(ref)
    except Exception as exc:
        echo_error("delete_failed", str(exc))
    echo_json({"ok": True, "deployment": deployment})


def deploy_command(
    payload_path: Annotated[Path, typer.Argument(help="Path to schedule JSON payload.")],
    env: Annotated[str | None, typer.Option("--env", help="Environment name.")] = None,
) -> None:
    """Deploy or update a workflow schedule from JSON."""
    deploy_from_payload(payload_path, env=env)


def run_now_command(
    payload_path: Annotated[
        Path | None,
        typer.Option("--payload", help="Run workflow directly from JSON payload."),
    ] = None,
    deployment_ref: Annotated[
        str | None,
        typer.Option("--deployment", help="Deployment UUID or flow/deployment name."),
    ] = None,
    fake: Annotated[
        bool,
        typer.Option("--fake", help="Use fake runner for direct payload execution."),
    ] = False,
    env: Annotated[str | None, typer.Option("--env", help="Environment name.")] = None,
) -> None:
    """Run a workflow now from a deployment or direct JSON payload."""
    if payload_path is None and deployment_ref is None:
        echo_error("invalid_request", "Provide either --payload or --deployment.")
    if payload_path is not None and deployment_ref is not None:
        echo_error("invalid_request", "Use only one of --payload or --deployment.")

    try:
        if deployment_ref is not None:
            _apply_runtime_env(env)
            flow_run = _run_deployment_now(deployment_ref)
            echo_json({"ok": True, "flow_run": flow_run})
            return

        payload = read_json_file(payload_path)  # type: ignore[arg-type]
        result = _execute_payload_now(payload, fake=fake)
    except ValidationError as exc:
        echo_error("invalid_payload", "Payload validation failed.", validation_details(exc))
    except Exception as exc:
        echo_error("run_now_failed", str(exc))

    echo_json({"ok": True, "result": result})


def _execute_payload_now(payload: dict[str, Any], fake: bool) -> dict[str, Any]:
    from agent_scheduler.flows import execute_registered_workflow
    from agent_scheduler.runners import FakeRunnerAdapter

    spec = WorkflowDeploymentSpec.model_validate(payload)
    adapter = FakeRunnerAdapter() if fake else None
    result = execute_registered_workflow(
        spec.workflow_name,
        spec.params,
        runner=spec.runner,
        adapter=adapter,
    )
    return result.model_dump()


def _apply_runtime_env(env: str | None):
    settings = load_settings(env=env)
    apply_prefect_environment(settings)
    return settings


def _deploy_workflow(spec: WorkflowDeploymentSpec, global_concurrency_limit: int):
    from agent_scheduler.flows import deploy_workflow

    return deploy_workflow(spec, global_concurrency_limit=global_concurrency_limit)


def _list_deployments(limit: int, offset: int) -> list[dict[str, Any]]:
    from agent_scheduler.schedules.lifecycle import list_deployments

    return list_deployments(limit=limit, offset=offset)


def _inspect_deployment(ref: str) -> dict[str, Any]:
    from agent_scheduler.schedules.lifecycle import inspect_deployment

    return inspect_deployment(ref)


def _pause_deployment(ref: str) -> dict[str, Any]:
    from agent_scheduler.schedules.lifecycle import pause_deployment

    return pause_deployment(ref)


def _resume_deployment(ref: str) -> dict[str, Any]:
    from agent_scheduler.schedules.lifecycle import resume_deployment

    return resume_deployment(ref)


def _delete_deployment(ref: str) -> dict[str, Any]:
    from agent_scheduler.schedules.lifecycle import delete_deployment

    return delete_deployment(ref)


def _run_deployment_now(ref: str) -> dict[str, Any]:
    from agent_scheduler.schedules.lifecycle import run_deployment_now

    return run_deployment_now(ref)
