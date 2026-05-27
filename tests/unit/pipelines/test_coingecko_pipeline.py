import asyncio

from agent_scheduler.pipelines.coingecko.client import CoinGeckoClientConfig
from agent_scheduler.pipelines.coingecko.asset_platforms import ingest_asset_platforms
from agent_scheduler.pipelines.coingecko.coins_list import ingest_coins_list
from agent_scheduler.pipelines.coingecko.flows import (
    coingecko_ingest_asset_platforms_flow,
    coingecko_ingest_coins_flow,
    coingecko_ingest_nfts_list_flow,
)
from agent_scheduler.pipelines.coingecko.nfts_list import ingest_nfts_list
from agent_scheduler.pipelines.coingecko.repository import SCHEMA_SQL


def test_coingecko_schema_targets_public_data() -> None:
    assert "CREATE SCHEMA IF NOT EXISTS public_data" in SCHEMA_SQL
    assert "CREATE TABLE IF NOT EXISTS public_data.coingecko_coins" in SCHEMA_SQL
    assert (
        "CREATE TABLE IF NOT EXISTS public_data.coingecko_asset_platforms" in SCHEMA_SQL
    )
    assert "CREATE TABLE IF NOT EXISTS public_data.coingecko_nft_collections" in SCHEMA_SQL
    assert "CREATE TABLE IF NOT EXISTS public_data.pipeline_ingest_runs" in SCHEMA_SQL
    assert "trading_private" not in SCHEMA_SQL


def test_ingest_coins_list_dry_run_fetches_and_validates(monkeypatch) -> None:
    def fake_get_coins_list(self, *, include_platform, status):
        assert include_platform is True
        assert status == "active"
        return [
            {
                "id": "bitcoin",
                "symbol": "btc",
                "name": "Bitcoin",
                "platforms": {},
            }
        ]

    monkeypatch.setattr(
        "agent_scheduler.pipelines.coingecko.client.CoinGeckoClient.get_coins_list",
        fake_get_coins_list,
    )

    result = asyncio.run(
        ingest_coins_list(
            database_url="postgresql+asyncpg://pipeline_app:secret@postgres:5432/pipeline_data",
            client_config=CoinGeckoClientConfig(base_url="https://example.test/api/v3"),
            include_platform=True,
            dry_run=True,
        )
    )

    assert result.status == "dry_run"
    assert result.fetched_count == 1
    assert result.upserted_count == 0
    assert result.database_url == (
        "postgresql+asyncpg://pipeline_app:***@postgres:5432/pipeline_data"
    )


def test_coingecko_prefect_flow_names_are_stable() -> None:
    assert coingecko_ingest_coins_flow.name == "coingecko-ingest-coins"
    assert coingecko_ingest_asset_platforms_flow.name == (
        "coingecko-ingest-asset-platforms"
    )
    assert coingecko_ingest_nfts_list_flow.name == "coingecko-ingest-nfts-list"


def test_ingest_asset_platforms_dry_run_fetches_and_validates(monkeypatch) -> None:
    def fake_get_asset_platforms(self, *, filter_value):
        assert filter_value == "nft"
        return [
            {
                "id": "polygon-pos",
                "chain_identifier": 137,
                "name": "Polygon POS",
                "shortname": "MATIC",
                "native_coin_id": "matic-network",
                "image": {"thumb": "https://example.test/polygon.png", "small": None},
            }
        ]

    monkeypatch.setattr(
        "agent_scheduler.pipelines.coingecko.client.CoinGeckoClient.get_asset_platforms",
        fake_get_asset_platforms,
    )

    result = asyncio.run(
        ingest_asset_platforms(
            database_url="postgresql+asyncpg://pipeline_app:secret@postgres:5432/pipeline_data",
            client_config=CoinGeckoClientConfig(base_url="https://example.test/api/v3"),
            platform_filter="nft",
            dry_run=True,
        )
    )

    assert result.status == "dry_run"
    assert result.platform_filter == "nft"
    assert result.fetched_count == 1
    assert result.upserted_count == 0
    assert result.database_url == (
        "postgresql+asyncpg://pipeline_app:***@postgres:5432/pipeline_data"
    )


def test_ingest_nfts_list_dry_run_fetches_one_page_with_no_delay(monkeypatch) -> None:
    calls = []

    def fake_get_nfts_list(self, *, order, per_page, page):
        calls.append((order, per_page, page))
        return [
            {
                "id": "bored-ape-yacht-club",
                "contract_address": None,
                "name": "Bored Ape Yacht Club",
                "asset_platform_id": "ethereum",
                "symbol": "BAYC",
            }
        ]

    monkeypatch.setattr(
        "agent_scheduler.pipelines.coingecko.client.CoinGeckoClient.get_nfts_list",
        fake_get_nfts_list,
    )

    result = asyncio.run(
        ingest_nfts_list(
            database_url="postgresql+asyncpg://pipeline_app:secret@postgres:5432/pipeline_data",
            client_config=CoinGeckoClientConfig(base_url="https://example.test/api/v3"),
            order="market_cap_usd_desc",
            per_page=250,
            max_pages=1,
            request_delay_seconds=0,
            dry_run=True,
        )
    )

    assert calls == [("market_cap_usd_desc", 250, 1)]
    assert result.status == "dry_run"
    assert result.pages_fetched == 1
    assert result.fetched_count == 1
    assert result.upserted_count == 0
