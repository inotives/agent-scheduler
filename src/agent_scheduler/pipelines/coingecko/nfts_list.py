from __future__ import annotations

from datetime import UTC, datetime
from time import sleep
from typing import Any

import asyncpg
from pydantic import ValidationError

from agent_scheduler.pipelines.coingecko.client import (
    CoinGeckoClient,
    CoinGeckoClientConfig,
)
from agent_scheduler.pipelines.coingecko.models import (
    CoinGeckoNftCollection,
    CoinGeckoNftsListIngestResult,
)
from agent_scheduler.pipelines.coingecko.repository import (
    finish_ingest_run,
    prepare_schema,
    start_ingest_run,
    upsert_nft_collections,
)
from agent_scheduler.pipelines.common.database import redact_database_url, to_asyncpg_dsn


async def ingest_nfts_list(
    *,
    database_url: str,
    client_config: CoinGeckoClientConfig,
    order: str | None = None,
    per_page: int = 250,
    max_pages: int | None = None,
    request_delay_seconds: float = 6.0,
    dry_run: bool = False,
) -> CoinGeckoNftsListIngestResult:
    _validate_pagination(
        per_page=per_page,
        max_pages=max_pages,
        request_delay_seconds=request_delay_seconds,
    )
    started_at = datetime.now(UTC)
    client = CoinGeckoClient(client_config)
    raw_nfts = _fetch_all_nfts(
        client,
        order=order,
        per_page=per_page,
        max_pages=max_pages,
        request_delay_seconds=request_delay_seconds,
    )
    nft_collections = _parse_nft_collections(raw_nfts)
    pages_fetched = _pages_fetched(len(raw_nfts), per_page)

    if dry_run:
        completed_at = datetime.now(UTC)
        return CoinGeckoNftsListIngestResult(
            source="coingecko",
            status="dry_run",
            order=order,
            per_page=per_page,
            pages_fetched=pages_fetched,
            fetched_count=len(raw_nfts),
            upserted_count=0,
            ingest_run_id=0,
            started_at=started_at,
            completed_at=completed_at,
            database_url=redact_database_url(database_url),
            metadata={"validated_count": len(nft_collections), "max_pages": max_pages},
        )

    connection = await asyncpg.connect(to_asyncpg_dsn(database_url))
    ingest_run_id = 0
    try:
        await prepare_schema(connection)
        ingest_run_id = await start_ingest_run(
            connection,
            source="coingecko",
            dataset="nfts_list",
            metadata={
                "order": order,
                "per_page": per_page,
                "pages_fetched": pages_fetched,
                "max_pages": max_pages,
                "request_delay_seconds": request_delay_seconds,
                "api_base_url": client_config.base_url,
            },
        )
        async with connection.transaction():
            upserted_count = await upsert_nft_collections(
                connection,
                nft_collections=nft_collections,
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
    return CoinGeckoNftsListIngestResult(
        source="coingecko",
        status="succeeded",
        order=order,
        per_page=per_page,
        pages_fetched=pages_fetched,
        fetched_count=len(raw_nfts),
        upserted_count=upserted_count,
        ingest_run_id=ingest_run_id,
        started_at=started_at,
        completed_at=completed_at,
        database_url=redact_database_url(database_url),
    )


def _fetch_all_nfts(
    client: CoinGeckoClient,
    *,
    order: str | None,
    per_page: int,
    max_pages: int | None,
    request_delay_seconds: float,
) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    page = 1
    while max_pages is None or page <= max_pages:
        page_items = client.get_nfts_list(order=order, per_page=per_page, page=page)
        if not page_items:
            break
        items.extend(page_items)
        if len(page_items) < per_page:
            break
        if request_delay_seconds:
            sleep(request_delay_seconds)
        page += 1
    return items


def _parse_nft_collections(
    raw_nfts: list[dict[str, Any]],
) -> list[CoinGeckoNftCollection]:
    nft_collections: list[CoinGeckoNftCollection] = []
    errors: list[str] = []
    for index, raw_nft in enumerate(raw_nfts):
        try:
            nft_collections.append(CoinGeckoNftCollection.model_validate(raw_nft))
        except ValidationError as exc:
            errors.append(f"item {index}: {exc.errors(include_url=False)}")

    if errors:
        raise ValueError(f"Invalid CoinGecko NFT payload: {'; '.join(errors[:5])}")
    return nft_collections


def _validate_pagination(
    *,
    per_page: int,
    max_pages: int | None,
    request_delay_seconds: float,
) -> None:
    if per_page < 1 or per_page > 250:
        raise ValueError("per_page must be between 1 and 250")
    if max_pages is not None and max_pages < 1:
        raise ValueError("max_pages must be at least 1")
    if request_delay_seconds < 0:
        raise ValueError("request_delay_seconds must be non-negative")


def _pages_fetched(item_count: int, per_page: int) -> int:
    if item_count == 0:
        return 0
    return (item_count + per_page - 1) // per_page
