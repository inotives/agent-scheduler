from __future__ import annotations

import json
import logging
from contextlib import nullcontext
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from prefect import flow, get_run_logger
from prefect.concurrency.sync import concurrency
from prefect.context import get_run_context
from prefect.exceptions import MissingContextError

from agent_scheduler.concurrency import runtime_concurrency_keys
from agent_scheduler.registry import RenderedWorkflow, default_registry
from agent_scheduler.runners import RunnerAdapter, RunnerContext, RunnerMetadata, RunnerResult, runner_for


def execute_registered_workflow(
    workflow_name: str,
    params: dict[str, Any],
    runner: str | None = None,
    adapter: RunnerAdapter | None = None,
) -> RunnerResult:
    rendered = default_registry().render(workflow_name, params, runner=runner)  # type: ignore[arg-type]
    selected_adapter = adapter or runner_for(rendered.runner)
    context = _runner_context(rendered)
    logger = _logger()

    logger.info("Starting agent workflow '%s' with runner '%s'", rendered.name, rendered.runner)
    started_at = datetime.now(timezone.utc)
    with _concurrency_context(rendered):
        result = selected_adapter.run(context, timeout_seconds=rendered.policy.timeout_seconds)
    _log_runner_result(result)

    if not result.succeeded:
        raise RuntimeError(
            f"Agent workflow '{rendered.name}' failed with status {result.status} "
            f"and exit code {result.exit_code}"
        )
    _verify_completion_signal(rendered, result, started_at)
    return result


@flow(name="agent-scheduler-run-workflow", log_prints=True)
def run_agent_workflow(
    workflow_name: str,
    params: dict[str, Any],
    runner: str | None = None,
) -> dict[str, Any]:
    result = execute_registered_workflow(workflow_name, params, runner=runner)
    return result.model_dump()


def _runner_context(rendered: RenderedWorkflow) -> RunnerContext:
    return RunnerContext(
        task_name=rendered.name,
        params=rendered.params.model_dump(mode="json"),
        workspace=rendered.workspace,
        runner=rendered.runner,
        prompt=rendered.prompt,
        metadata=_runner_metadata(),
    )


def _runner_metadata() -> RunnerMetadata:
    try:
        context = get_run_context()
    except MissingContextError:
        return RunnerMetadata()

    flow_run = getattr(context, "flow_run", None)
    deployment_id = getattr(flow_run, "deployment_id", None)
    attempt = getattr(flow_run, "run_count", None) or 1
    return RunnerMetadata(
        flow_run_id=str(getattr(flow_run, "id", "")) or None,
        deployment_id=str(deployment_id) if deployment_id else None,
        attempt=attempt,
    )


def _concurrency_context(rendered: RenderedWorkflow):
    if _is_prefect_run():
        return concurrency(
            runtime_concurrency_keys(rendered),
            occupy=1,
            timeout_seconds=None,
            strict=False,
        )
    return nullcontext()


def _is_prefect_run() -> bool:
    try:
        get_run_context()
    except MissingContextError:
        return False
    return True


def _log_runner_result(result: RunnerResult) -> None:
    logger = _logger()
    if result.stdout:
        logger.info("Runner stdout:\n%s", result.stdout)
    if result.stderr:
        logger.warning("Runner stderr:\n%s", result.stderr)
    logger.info(
        "Runner completed with status '%s' and exit code '%s'",
        result.status,
        result.exit_code,
    )


def _verify_completion_signal(
    rendered: RenderedWorkflow,
    result: RunnerResult,
    started_at: datetime,
) -> None:
    signal_path = getattr(rendered.params, "completion_signal_path", None)
    if signal_path is None or result.runner == "fake":
        return

    path = Path(signal_path)
    if not path.is_absolute():
        path = rendered.workspace / path
    if not path.exists():
        raise RuntimeError(f"completion signal was not written: {path}")

    modified_at = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
    if modified_at < started_at - timedelta(seconds=2):
        raise RuntimeError(f"completion signal is stale: {path}")

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"completion signal is not valid JSON: {path}") from exc

    status = str(payload.get("status", "")).lower()
    if status not in {"completed", "succeeded", "success"}:
        raise RuntimeError(f"completion signal status is not successful: {path}")

    _logger().info("Completion signal verified at %s", path)


def _logger() -> logging.Logger:
    try:
        return get_run_logger()
    except MissingContextError:
        return logging.getLogger("agent_scheduler.flows")
