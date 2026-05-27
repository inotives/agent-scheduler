from __future__ import annotations

from agent_scheduler.runners.subprocess import SubprocessRunnerAdapter


class CodexRunnerAdapter(SubprocessRunnerAdapter):
    def __init__(self, executable: str = "codex") -> None:
        super().__init__(
            runner="codex",
            executable=executable,
            args=("exec", "--full-auto", "-"),
        )

