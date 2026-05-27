"""Headless agent runner adapters."""

from agent_scheduler.runners.base import RunnerAdapter
from agent_scheduler.runners.claude import ClaudeRunnerAdapter
from agent_scheduler.runners.codex import CodexRunnerAdapter
from agent_scheduler.runners.errors import RunnerError, UnknownRunnerError
from agent_scheduler.runners.factory import runner_for
from agent_scheduler.runners.fake import FakeRunnerAdapter
from agent_scheduler.runners.opencode import OpenCodeRunnerAdapter
from agent_scheduler.runners.types import RunnerContext, RunnerMetadata, RunnerResult

__all__ = [
    "CodexRunnerAdapter",
    "ClaudeRunnerAdapter",
    "FakeRunnerAdapter",
    "OpenCodeRunnerAdapter",
    "RunnerAdapter",
    "RunnerContext",
    "RunnerError",
    "RunnerMetadata",
    "RunnerResult",
    "UnknownRunnerError",
    "runner_for",
]
