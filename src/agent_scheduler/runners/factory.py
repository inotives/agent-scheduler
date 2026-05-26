from __future__ import annotations

from agent_scheduler.registry import RunnerType
from agent_scheduler.runners.base import RunnerAdapter
from agent_scheduler.runners.codex import CodexRunnerAdapter
from agent_scheduler.runners.errors import UnknownRunnerError
from agent_scheduler.runners.opencode import OpenCodeRunnerAdapter


def runner_for(runner: RunnerType) -> RunnerAdapter:
    if runner == "codex":
        return CodexRunnerAdapter()
    if runner == "opencode":
        return OpenCodeRunnerAdapter()
    raise UnknownRunnerError(runner)

