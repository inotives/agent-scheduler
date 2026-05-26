class RegistryError(Exception):
    """Base error for workflow registry failures."""


class UnknownWorkflowError(RegistryError):
    def __init__(self, workflow_name: str) -> None:
        super().__init__(f"Unknown workflow: {workflow_name}")
        self.workflow_name = workflow_name


class DuplicateWorkflowError(RegistryError):
    def __init__(self, workflow_name: str) -> None:
        super().__init__(f"Duplicate workflow: {workflow_name}")
        self.workflow_name = workflow_name

