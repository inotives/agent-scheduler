from agent_scheduler.pipelines.common.database import (
    redact_database_url,
    to_asyncpg_dsn,
)


def test_to_asyncpg_dsn_removes_sqlalchemy_driver() -> None:
    assert (
        to_asyncpg_dsn("postgresql+asyncpg://user:pass@localhost:5432/pipeline_data")
        == "postgresql://user:pass@localhost:5432/pipeline_data"
    )


def test_redact_database_url_hides_password() -> None:
    assert (
        redact_database_url("postgresql+asyncpg://user:secret@localhost:5432/pipeline_data")
        == "postgresql+asyncpg://user:***@localhost:5432/pipeline_data"
    )
