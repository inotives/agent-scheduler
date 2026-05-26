from types import SimpleNamespace
from uuid import uuid4

from agent_scheduler.schedules import lifecycle


class FakeClient:
    def __init__(self, deployment):
        self.deployment = deployment
        self.paused = False
        self.resumed = False
        self.deleted = False

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return None

    def read_deployment(self, deployment_id):
        return self.deployment

    def read_deployment_by_name(self, name):
        return self.deployment

    def read_deployments(self, limit, offset):
        return [self.deployment]

    def pause_deployment(self, deployment_id):
        self.paused = True

    def resume_deployment(self, deployment_id):
        self.resumed = True

    def delete_deployment(self, deployment_id):
        self.deleted = True

    def create_flow_run_from_deployment(self, deployment_id, parameters=None):
        return SimpleNamespace(
            id=uuid4(),
            name="manual-run",
            deployment_id=deployment_id,
            state=SimpleNamespace(type="SCHEDULED", name="Scheduled"),
        )


def test_lifecycle_summaries(monkeypatch) -> None:
    deployment = SimpleNamespace(
        id=uuid4(),
        name="daily-gemi-close",
        flow_id=uuid4(),
        paused=False,
        work_pool_name="agent-scheduler",
        work_queue_name=None,
        parameters={"workflow_name": "run_skill_for_assets"},
        tags=["agent-scheduler"],
    )
    client = FakeClient(deployment)
    monkeypatch.setattr(lifecycle, "get_client", lambda sync_client: client)

    assert lifecycle.list_deployments()[0]["id"] == str(deployment.id)
    assert lifecycle.inspect_deployment(str(deployment.id))["name"] == "daily-gemi-close"
    assert lifecycle.pause_deployment(str(deployment.id))["paused"] is True
    assert client.paused is True
    assert lifecycle.resume_deployment(str(deployment.id))["paused"] is False
    assert client.resumed is True
    assert lifecycle.delete_deployment(str(deployment.id))["id"] == str(deployment.id)
    assert client.deleted is True

    flow_run = lifecycle.run_deployment_now(str(deployment.id))
    assert flow_run["deployment_id"] == str(deployment.id)
    assert flow_run["state_name"] == "Scheduled"
