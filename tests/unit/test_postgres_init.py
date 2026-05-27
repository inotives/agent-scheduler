from pathlib import Path


def test_postgres_init_defines_separate_databases_and_schemas() -> None:
    script = Path("infra/postgres/init/010-create-databases.sh").read_text()

    assert "PREFECT_DB_NAME" in script
    assert "AGENT_SCHEDULER_DB_NAME" in script
    assert "PIPELINE_DB_NAME" in script
    assert "CREATE SCHEMA IF NOT EXISTS scheduler_app" in script
    assert "CREATE SCHEMA IF NOT EXISTS pipeline_app" in script
    assert "CREATE SCHEMA IF NOT EXISTS public_data" in script
    assert "CREATE SCHEMA IF NOT EXISTS trading_private" in script


def test_postgres_init_keeps_trading_private_schema_restricted() -> None:
    script = Path("infra/postgres/init/010-create-databases.sh").read_text()

    assert "REVOKE ALL ON SCHEMA trading_private FROM PUBLIC" in script
    assert 'REVOKE ALL ON SCHEMA trading_private FROM :"pipeline_user"' in script
    assert 'REVOKE ALL ON SCHEMA trading_private FROM :"analytics_user"' in script
    assert 'GRANT USAGE, CREATE ON SCHEMA trading_private TO :"trading_user"' in script
