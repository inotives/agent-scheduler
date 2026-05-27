from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import asyncpg
from pydantic import ValidationError

from agent_scheduler.pipelines.coingecko.client import (
    CoinGeckoClient,
    CoinGeckoClientConfig,
)
from agent_scheduler.pipelines.coingecko.models import (
    CoinGeckoCoin,
    CoinGeckoCoinsListIngestResult,
)
from agent_scheduler.pipelines.coingecko.repository import (
    finish_ingest_run,
    prepare_schema,
    start_ingest_run,
    upsert_coins,
)
from agent_scheduler.pipelines.common.database import redact_database_url, to_asyncpg_dsn


async def ingest_coins_list(
    *,
    database_url: str,
    client_config: CoinGeckoClientConfig,
    include_platform: bool = False,
    coin_status: str = "active",
    dry_run: bool = False,
) -> CoinGeckoCoinsListIngestResult:
    started_at = datetime.now(UTC)
    client = CoinGeckoClient(client_config)
    raw_coins = client.get_coins_list(
        include_platform=include_platform,
        status=coin_status,
    )
    coins = _parse_coins(raw_coins)

    if dry_run:
        completed_at = datetime.now(UTC)
        return CoinGeckoCoinsListIngestResult(
            source="coingecko",
            status="dry_run",
            include_platform=include_platform,
            coin_status=coin_status,
            fetched_count=len(raw_coins),
            upserted_count=0,
            ingest_run_id=0,
            started_at=started_at,
            completed_at=completed_at,
            database_url=redact_database_url(database_url),
            metadata={"validated_count": len(coins)},
        )

    connection = await asyncpg.connect(to_asyncpg_dsn(database_url))
    ingest_run_id = 0
    try:
        await prepare_schema(connection)
        ingest_run_id = await start_ingest_run(
            connection,
            source="coingecko",
            dataset="coins_list",
            metadata={
                "include_platform": include_platform,
                "coin_status": coin_status,
                "api_base_url": client_config.base_url,
            },
        )
        async with connection.transaction():
            upserted_count = await upsert_coins(
                connection,
                coins=coins,
                status=coin_status,
            )
        await finish_ingest_run(
            connection,
            ingest_run_id=ingest_run_id,
            status="succeeded",
            row_count=upserted_count,
        )
    except Exception as exc:
        if ingest_run_id:
            await finish_ingest_run(
                connection,
                ingest_run_id=ingest_run_id,
                status="failed",
                row_count=0,
                error=str(exc),
            )
        raise
    finally:
        await connection.close()

    completed_at = datetime.now(UTC)
    return CoinGeckoCoinsListIngestResult(
        source="coingecko",
        status="succeeded",
        include_platform=include_platform,
        coin_status=coin_status,
        fetched_count=len(raw_coins),
        upserted_count=upserted_count,
        ingest_run_id=ingest_run_id,
        started_at=started_at,
        completed_at=completed_at,
        database_url=redact_database_url(database_url),
    )


def _parse_coins(raw_coins: list[dict[str, Any]]) -> list[CoinGeckoCoin]:
    coins: list[CoinGeckoCoin] = []
    errors: list[str] = []
    for index, raw_coin in enumerate(raw_coins):
        try:
            coins.append(CoinGeckoCoin.model_validate(raw_coin))
        except ValidationError as exc:
            errors.append(f"item {index}: {exc.errors(include_url=False)}")

    if errors:
        raise ValueError(f"Invalid CoinGecko coin payload: {'; '.join(errors[:5])}")
    return coins
