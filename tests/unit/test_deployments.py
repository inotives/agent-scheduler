from pathlib import Path
from uuid import uuid4

from agent_scheduler.flows import deployments
from agent_scheduler.schedules import WorkflowDeploymentSpec


def test_deploy_workflow_sets_process_worker_working_dir(monkeypatch) -> None:
    deployment_id = uuid4()
    calls = {}

    class FakeDeployment:
        def apply(self, work_pool_name):
            calls["apply_work_pool_name"] = work_pool_name
            return deployment_id

    class FakeFlow:
        def with_options(self, **kwargs):
            calls["flow_options"] = kwargs
            return self

        def to_deployment(self, **kwargs):
            calls["deployment_kwargs"] = kwargs
            return FakeDeployment()

    monkeypatch.setattr(deployments, "run_agent_workflow", FakeFlow())
    monkeypatch.setattr(deployments, "upsert_runtime_concurrency_limits", lambda *args, **kwargs: None)
    monkeypatch.setattr(deployments, "ensure_work_pool", lambda *args, **kwargs: None)

    result = deployments.deploy_workflow(
        WorkflowDeploymentSpec.model_validate(
            {
                "name": "daily-stock-market-close-summary",
                "task": "run_skill_for_assets",
                "schedule": {
                    "type": "cron",
                    "cron": "0 16 * * *",
                    "timezone": "Asia/Singapore",
                },
                "params": {"path_to_skill": "/skills/audit", "assets": ["GEMI"]},
            }
        )
    )

    assert result == deployment_id
    assert calls["flow_options"] == {
        "retries": 0,
        "retry_delay_seconds": 60,
        "timeout_seconds": 3630,
    }
    assert calls["deployment_kwargs"]["job_variables"] == {"working_dir": str(Path.cwd())}
    assert calls["apply_work_pool_name"] == "agent-scheduler"
