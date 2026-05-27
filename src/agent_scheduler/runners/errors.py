class RunnerError(Exception):
    """Base error for runner failures."""


class UnknownRunnerError(RunnerError):
    def __init__(self, runner_name: str) -> None:
        super().__init__(f"Unknown runner: {runner_name}")
        self.runner_name = runner_name

