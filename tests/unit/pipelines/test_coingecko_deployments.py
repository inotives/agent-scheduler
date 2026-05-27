from pathlib import Path
from uuid import uuid4
import importlib.util


def _load_deploy_schedules_module():
    module_path = Path("pipelines/coingecko/deploy_schedules.py")
    spec = importlib.util.spec_from_file_location("coingecko_deploy_schedules", module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_deploy_coingecko_schedules_uses_weekly_sunday_10am(monkeypatch, capsys) -> None:
    deploy_schedules = _load_deploy_schedules_module()
    deployment_ids = [uuid4(), uuid4(), uuid4()]
    calls = []

    class FakeDeployment:
        def apply(self, work_pool_name):
            return deployment_ids.pop(0)

    class FakeFlow:
        def __init__(self, flow_name: str) -> None:
            self.flow_name = flow_name

        def to_deployment(self, **kwargs):
            calls.append((self.flow_name, kwargs))
            return FakeDeployment()

    monkeypatch.setattr(deploy_schedules, "ensure_work_pool", lambda work_pool_name: None)
    monkeypatch.setattr(
        deploy_schedules,
        "coingecko_ingest_coins_flow",
        FakeFlow("coingecko-ingest-coins"),
    )
    monkeypatch.setattr(
        deploy_schedules,
        "coingecko_ingest_asset_platforms_flow",
        FakeFlow("coingecko-ingest-asset-platforms"),
    )
    monkeypatch.setattr(
        deploy_schedules,
        "coingecko_ingest_nfts_list_flow",
        FakeFlow("coingecko-ingest-nfts-list"),
    )
    monkeypatch.setenv(
        "PIPELINE_DATABASE_URL",
        "postgresql+asyncpg://pipeline_app:pipeline_app@127.0.0.1:5432/pipeline_data",
    )
    monkeypatch.setattr("sys.argv", ["deploy_schedules.py"])

    deploy_schedules.main()

    assert calls[0][1]["name"] == "weekly-coingecko-coins-list"
    assert calls[1][1]["name"] == "weekly-coingecko-asset-platforms"
    assert calls[2][1]["name"] == "weekly-coingecko-nfts-list"
    assert calls[0][1]["schedule"].cron == "0 10 * * 0"
    assert calls[0][1]["schedule"].timezone == "Asia/Singapore"
    assert calls[0][1]["job_variables"] == {
        "working_dir": str(Path.cwd()),
        "env": {
            "PIPELINE_DATABASE_URL": (
                "postgresql+asyncpg://pipeline_app:pipeline_app@127.0.0.1:5432/pipeline_data"
            )
        },
    }
    assert calls[0][1]["parameters"] == {
        "include_platform": True,
        "coin_status": "active",
    }
    assert calls[1][1]["parameters"] == {"platform_filter": None}
    assert calls[2][1]["parameters"] == {
        "order": None,
        "per_page": 250,
        "max_pages": None,
    }
    assert '"ok": true' in capsys.readouterr().out
