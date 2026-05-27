from __future__ import annotations

from agent_scheduler.runners.base import RunnerAdapter
from agent_scheduler.runners.types import RunnerContext, RunnerResult


class FakeRunnerAdapter(RunnerAdapter):
    def __init__(self, exit_code: int = 0, stdout: str | None = None, stderr: str = "") -> None:
        self.exit_code = exit_code
        self.stdout = stdout
        self.stderr = stderr

    def run(self, context: RunnerContext, timeout_seconds: int) -> RunnerResult:
        stdout = self.stdout if self.stdout is not None else context.to_json_payload()
        return RunnerResult(
            runner="fake",
            status="succeeded" if self.exit_code == 0 else "failed",
            exit_code=self.exit_code,
            stdout=stdout,
            stderr=self.stderr,
        )

