from __future__ import annotations

from agent_scheduler.runners.subprocess import SubprocessRunnerAdapter
from agent_scheduler.runners.types import RunnerContext


class OpenCodeRunnerAdapter(SubprocessRunnerAdapter):
    def __init__(self, executable: str = "opencode") -> None:
        super().__init__(
            runner="opencode",
            executable=executable,
            args=("run",),
        )

    def build_argv(self, context: RunnerContext) -> list[str]:
        return [self.executable, *self.args, context.prompt]

    def prompt_input(self, context: RunnerContext) -> None:
        return None
