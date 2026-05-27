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
    CoinGeckoAssetPlatform,
    CoinGeckoAssetPlatformsIngestResult,
)
from agent_scheduler.pipelines.coingecko.repository import (
    finish_ingest_run,
    prepare_schema,
    start_ingest_run,
    upsert_asset_platforms,
)
from agent_scheduler.pipelines.common.database import redact_database_url, to_asyncpg_dsn


async def ingest_asset_platforms(
    *,
    database_url: str,
    client_config: CoinGeckoClientConfig,
    platform_filter: str | None = None,
    dry_run: bool = False,
) -> CoinGeckoAssetPlatformsIngestResult:
    started_at = datetime.now(UTC)
    client = CoinGeckoClient(client_config)
    raw_asset_platforms = client.get_asset_platforms(filter_value=platform_filter)
    asset_platforms = _parse_asset_platforms(raw_asset_platforms)

    if dry_run:
        completed_at = datetime.now(UTC)
        return CoinGeckoAssetPlatformsIngestResult(
            source="coingecko",
            status="dry_run",
            platform_filter=platform_filter,
            fetched_count=len(raw_asset_platforms),
            upserted_count=0,
            ingest_run_id=0,
            started_at=started_at,
            completed_at=completed_at,
            database_url=redact_database_url(database_url),
            metadata={"validated_count": len(asset_platforms)},
        )

    connection = await asyncpg.connect(to_asyncpg_dsn(database_url))
    ingest_run_id = 0
    try:
        await prepare_schema(connection)
        ingest_run_id = await start_ingest_run(
            connection,
            source="coingecko",
            dataset="asset_platforms",
            metadata={
                "platform_filter": platform_filter,
                "api_base_url": client_config.base_url,
            },
        )
        async with connection.transaction():
            upserted_count = await upsert_asset_platforms(
                connection,
                asset_platforms=asset_platforms,
                platform_filter=platform_filter,
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
    return CoinGeckoAssetPlatformsIngestResult(
        source="coingecko",
        status="succeeded",
        platform_filter=platform_filter,
        fetched_count=len(raw_asset_platforms),
        upserted_count=upserted_count,
        ingest_run_id=ingest_run_id,
        started_at=started_at,
        completed_at=completed_at,
        database_url=redact_database_url(database_url),
    )


def _parse_asset_platforms(
    raw_asset_platforms: list[dict[str, Any]],
) -> list[CoinGeckoAssetPlatform]:
    asset_platforms: list[CoinGeckoAssetPlatform] = []
    errors: list[str] = []
    for index, raw_asset_platform in enumerate(raw_asset_platforms):
        try:
            asset_platforms.append(CoinGeckoAssetPlatform.model_validate(raw_asset_platform))
        except ValidationError as exc:
            errors.append(f"item {index}: {exc.errors(include_url=False)}")

    if errors:
        raise ValueError(
            f"Invalid CoinGecko asset platform payload: {'; '.join(errors[:5])}"
        )
    return asset_platforms
