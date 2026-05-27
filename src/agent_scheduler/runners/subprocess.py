from __future__ import annotations

import subprocess
from pathlib import Path

from agent_scheduler.registry import RunnerType
from agent_scheduler.runners.base import RunnerAdapter
from agent_scheduler.runners.types import RunnerContext, RunnerResult


class SubprocessRunnerAdapter(RunnerAdapter):
    runner: RunnerType
    executable: str
    args: tuple[str, ...]

    def __init__(self, runner: RunnerType, executable: str, args: tuple[str, ...]) -> None:
        self.runner = runner
        self.executable = executable
        self.args = args

    def build_argv(self, context: RunnerContext) -> list[str]:
        return [self.executable, *self.args]

    def prompt_input(self, context: RunnerContext) -> str | None:
        return context.prompt

    def run(self, context: RunnerContext, timeout_seconds: int) -> RunnerResult:
        prompt_input = self.prompt_input(context)
        stdin = subprocess.DEVNULL if prompt_input is None else None
        try:
            run_kwargs = {
                "text": True,
                "capture_output": True,
                "cwd": Path(context.workspace),
                "timeout": timeout_seconds,
                "check": False,
            }
            if prompt_input is None:
                run_kwargs["stdin"] = stdin
            else:
                run_kwargs["input"] = prompt_input

            completed = subprocess.run(self.build_argv(context), **run_kwargs)
        except subprocess.TimeoutExpired as exc:
            return RunnerResult(
                runner=self.runner,
                status="timed_out",
                exit_code=None,
                stdout=exc.stdout or "",
                stderr=exc.stderr or "",
                timed_out=True,
            )

        status = "succeeded" if completed.returncode == 0 else "failed"
        return RunnerResult(
            runner=self.runner,
            status=status,
            exit_code=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
        )
