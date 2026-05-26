from __future__ import annotations

from abc import ABC, abstractmethod

from agent_scheduler.runners.types import RunnerContext, RunnerResult


class RunnerAdapter(ABC):
    @abstractmethod
    def run(self, context: RunnerContext, timeout_seconds: int) -> RunnerResult:
        """Execute the rendered workflow prompt in headless mode."""

