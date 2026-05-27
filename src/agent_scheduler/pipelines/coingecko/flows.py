from __future__ import annotations

import asyncio
from typing import Any

from prefect import flow

from agent_scheduler.config.settings import load_settings
from agent_scheduler.pipelines.coingecko.asset_platforms import ingest_asset_platforms
from agent_scheduler.pipelines.coingecko.client import CoinGeckoClientConfig
from agent_scheduler.pipelines.coingecko.coins_list import ingest_coins_list
from agent_scheduler.pipelines.coingecko.nfts_list import ingest_nfts_list


def _client_config(env: str | None) -> tuple[str, CoinGeckoClientConfig]:
    settings = load_settings(env=env)
    return (
        settings.pipeline_database_url,
        CoinGeckoClientConfig(
            base_url=settings.coingecko_api_base_url,
            api_key=settings.coingecko_api_key,
            api_key_header=settings.coingecko_api_key_header,
            timeout_seconds=settings.coingecko_request_timeout_seconds,
        ),
    )


@flow(name="coingecko-ingest-coins", log_prints=True)
def coingecko_ingest_coins_flow(
    include_platform: bool = True,
    coin_status: str = "active",
    env: str | None = None,
) -> dict[str, Any]:
    database_url, client_config = _client_config(env)
    result = asyncio.run(
        ingest_coins_list(
            database_url=database_url,
            client_config=client_config,
            include_platform=include_platform,
            coin_status=coin_status,
        )
    )
    return result.model_dump(mode="json")


@flow(name="coingecko-ingest-asset-platforms", log_prints=True)
def coingecko_ingest_asset_platforms_flow(
    platform_filter: str | None = None,
    env: str | None = None,
) -> dict[str, Any]:
    database_url, client_config = _client_config(env)
    result = asyncio.run(
        ingest_asset_platforms(
            database_url=database_url,
            client_config=client_config,
            platform_filter=platform_filter,
        )
    )
    return result.model_dump(mode="json")


@flow(name="coingecko-ingest-nfts-list", log_prints=True)
def coingecko_ingest_nfts_list_flow(
    order: str | None = None,
    per_page: int = 250,
    max_pages: int | None = None,
    env: str | None = None,
) -> dict[str, Any]:
    settings = load_settings(env=env)
    result = asyncio.run(
        ingest_nfts_list(
            database_url=settings.pipeline_database_url,
            client_config=CoinGeckoClientConfig(
                base_url=settings.coingecko_api_base_url,
                api_key=settings.coingecko_api_key,
                api_key_header=settings.coingecko_api_key_header,
                timeout_seconds=settings.coingecko_request_timeout_seconds,
            ),
            order=order,
            per_page=per_page,
            max_pages=max_pages,
            request_delay_seconds=settings.coingecko_paginated_request_delay_seconds,
        )
    )
    return result.model_dump(mode="json")
