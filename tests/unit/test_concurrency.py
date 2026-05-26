from agent_scheduler.concurrency import (
    GLOBAL_CONCURRENCY_KEY,
    concurrency_key,
    runtime_concurrency_keys,
    upsert_runtime_concurrency_limits,
)
from agent_scheduler.registry import default_registry


def test_runtime_concurrency_keys_include_global_and_task_workspace() -> None:
    rendered = default_registry().render(
        "run_skill_for_assets",
        {"path_to_skill": "/skills/audit", "assets": ["GEMI"]},
    )

    assert runtime_concurrency_keys(rendered) == [
        GLOBAL_CONCURRENCY_KEY,
        concurrency_key(rendered),
    ]
    assert rendered.name in runtime_concurrency_keys(rendered)[1]


def test_upsert_runtime_concurrency_limits(monkeypatch) -> None:
    rendered = default_registry().render(
        "run_skill_for_assets",
        {"path_to_skill": "/skills/audit", "assets": ["GEMI"]},
    )
    calls = []

    class FakeClient:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return None

        def upsert_global_concurrency_limit_by_name(self, name, limit):
            calls.append((name, limit))

    monkeypatch.setattr(
        "agent_scheduler.concurrency.limits.get_client",
        lambda sync_client: FakeClient(),
    )

    upsert_runtime_concurrency_limits(rendered, global_limit=4)

    assert calls == [
        (GLOBAL_CONCURRENCY_KEY, 4),
        (concurrency_key(rendered), rendered.policy.concurrency_limit),
    ]
