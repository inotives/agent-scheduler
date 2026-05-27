from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

import asyncpg

from agent_scheduler.pipelines.coingecko.models import (
    CoinGeckoAssetPlatform,
    CoinGeckoCoin,
    CoinGeckoNftCollection,
)


SCHEMA_SQL = """
CREATE SCHEMA IF NOT EXISTS public_data;

CREATE TABLE IF NOT EXISTS public_data.pipeline_ingest_runs (
    id bigserial PRIMARY KEY,
    source text NOT NULL,
    dataset text NOT NULL,
    status text NOT NULL,
    started_at timestamptz NOT NULL DEFAULT now(),
    completed_at timestamptz,
    row_count integer NOT NULL DEFAULT 0,
    metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
    error text
);

CREATE TABLE IF NOT EXISTS public_data.coingecko_coins (
    id text PRIMARY KEY,
    symbol text NOT NULL,
    name text NOT NULL,
    platforms jsonb NOT NULL DEFAULT '{}'::jsonb,
    status text NOT NULL,
    source text NOT NULL DEFAULT 'coingecko',
    first_seen_at timestamptz NOT NULL DEFAULT now(),
    last_seen_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS coingecko_coins_symbol_idx
    ON public_data.coingecko_coins (symbol);
CREATE INDEX IF NOT EXISTS coingecko_coins_status_idx
    ON public_data.coingecko_coins (status);

CREATE TABLE IF NOT EXISTS public_data.coingecko_asset_platforms (
    id text PRIMARY KEY,
    chain_identifier integer,
    name text NOT NULL,
    shortname text,
    native_coin_id text,
    image jsonb NOT NULL DEFAULT '{}'::jsonb,
    platform_filter text,
    source text NOT NULL DEFAULT 'coingecko',
    first_seen_at timestamptz NOT NULL DEFAULT now(),
    last_seen_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS coingecko_asset_platforms_chain_identifier_idx
    ON public_data.coingecko_asset_platforms (chain_identifier);
CREATE INDEX IF NOT EXISTS coingecko_asset_platforms_native_coin_id_idx
    ON public_data.coingecko_asset_platforms (native_coin_id);

CREATE TABLE IF NOT EXISTS public_data.coingecko_nft_collections (
    id text PRIMARY KEY,
    contract_address text,
    name text NOT NULL,
    asset_platform_id text NOT NULL,
    symbol text,
    source text NOT NULL DEFAULT 'coingecko',
    first_seen_at timestamptz NOT NULL DEFAULT now(),
    last_seen_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS coingecko_nft_collections_contract_address_idx
    ON public_data.coingecko_nft_collections (contract_address);
CREATE INDEX IF NOT EXISTS coingecko_nft_collections_asset_platform_id_idx
    ON public_data.coingecko_nft_collections (asset_platform_id);
"""


async def prepare_schema(connection: asyncpg.Connection) -> None:
    await connection.execute(SCHEMA_SQL)


async def start_ingest_run(
    connection: asyncpg.Connection,
    *,
    source: str,
    dataset: str,
    metadata: dict[str, Any],
) -> int:
    return await connection.fetchval(
        """
        INSERT INTO public_data.pipeline_ingest_runs
            (source, dataset, status, started_at, metadata)
        VALUES ($1, $2, 'running', $3, $4::jsonb)
        RETURNING id
        """,
        source,
        dataset,
        datetime.now(UTC),
        json.dumps(metadata),
    )


async def finish_ingest_run(
    connection: asyncpg.Connection,
    *,
    ingest_run_id: int,
    status: str,
    row_count: int,
    error: str | None = None,
) -> None:
    await connection.execute(
        """
        UPDATE public_data.pipeline_ingest_runs
        SET status = $2,
            completed_at = $3,
            row_count = $4,
            error = $5
        WHERE id = $1
        """,
        ingest_run_id,
        status,
        datetime.now(UTC),
        row_count,
        error,
    )


async def upsert_coins(
    connection: asyncpg.Connection,
    *,
    coins: list[CoinGeckoCoin],
    status: str,
) -> int:
    records = [
        (
            coin.id,
            coin.symbol,
            coin.name,
            json.dumps(dict(coin.platforms)),
            status,
            datetime.now(UTC),
        )
        for coin in coins
    ]
    if not records:
        return 0

    await connection.executemany(
        """
        INSERT INTO public_data.coingecko_coins
            (id, symbol, name, platforms, status, last_seen_at, updated_at)
        VALUES ($1, $2, $3, $4::jsonb, $5, $6, $6)
        ON CONFLICT (id) DO UPDATE SET
            symbol = EXCLUDED.symbol,
            name = EXCLUDED.name,
            platforms = EXCLUDED.platforms,
            status = EXCLUDED.status,
            last_seen_at = EXCLUDED.last_seen_at,
            updated_at = EXCLUDED.updated_at
        """,
        records,
    )
    return len(records)


async def upsert_asset_platforms(
    connection: asyncpg.Connection,
    *,
    asset_platforms: list[CoinGeckoAssetPlatform],
    platform_filter: str | None,
) -> int:
    records = [
        (
            platform.id,
            platform.chain_identifier,
            platform.name,
            platform.shortname,
            platform.native_coin_id,
            json.dumps(dict(platform.image)),
            platform_filter,
            datetime.now(UTC),
        )
        for platform in asset_platforms
    ]
    if not records:
        return 0

    await connection.executemany(
        """
        INSERT INTO public_data.coingecko_asset_platforms
            (
                id,
                chain_identifier,
                name,
                shortname,
                native_coin_id,
                image,
                platform_filter,
                last_seen_at,
                updated_at
            )
        VALUES ($1, $2, $3, $4, $5, $6::jsonb, $7, $8, $8)
        ON CONFLICT (id) DO UPDATE SET
            chain_identifier = EXCLUDED.chain_identifier,
            name = EXCLUDED.name,
            shortname = EXCLUDED.shortname,
            native_coin_id = EXCLUDED.native_coin_id,
            image = EXCLUDED.image,
            platform_filter = EXCLUDED.platform_filter,
            last_seen_at = EXCLUDED.last_seen_at,
            updated_at = EXCLUDED.updated_at
        """,
        records,
    )
    return len(records)


async def upsert_nft_collections(
    connection: asyncpg.Connection,
    *,
    nft_collections: list[CoinGeckoNftCollection],
) -> int:
    records = [
        (
            nft_collection.id,
            nft_collection.contract_address,
            nft_collection.name,
            nft_collection.asset_platform_id,
            nft_collection.symbol,
            datetime.now(UTC),
        )
        for nft_collection in nft_collections
    ]
    if not records:
        return 0

    await connection.executemany(
        """
        INSERT INTO public_data.coingecko_nft_collections
            (
                id,
                contract_address,
                name,
                asset_platform_id,
                symbol,
                last_seen_at,
                updated_at
            )
        VALUES ($1, $2, $3, $4, $5, $6, $6)
        ON CONFLICT (id) DO UPDATE SET
            contract_address = EXCLUDED.contract_address,
            name = EXCLUDED.name,
            asset_platform_id = EXCLUDED.asset_platform_id,
            symbol = EXCLUDED.symbol,
            last_seen_at = EXCLUDED.last_seen_at,
            updated_at = EXCLUDED.updated_at
        """,
        records,
    )
    return len(records)
