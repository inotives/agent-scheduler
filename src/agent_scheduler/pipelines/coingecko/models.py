from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class CoinGeckoCoin(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str = Field(min_length=1)
    symbol: str = Field(min_length=1)
    name: str = Field(min_length=1)
    platforms: dict[str, str] = Field(default_factory=dict)


class CoinGeckoAssetPlatform(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str
    chain_identifier: int | None = None
    name: str = Field(min_length=1)
    shortname: str | None = None
    native_coin_id: str | None = None
    image: dict[str, str | None] = Field(default_factory=dict)


class CoinGeckoNftCollection(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str = Field(min_length=1)
    contract_address: str | None = None
    name: str = Field(min_length=1)
    asset_platform_id: str = Field(min_length=1)
    symbol: str | None = None


class CoinGeckoCoinsListIngestResult(BaseModel):
    source: str
    status: str
    include_platform: bool
    coin_status: str
    fetched_count: int
    upserted_count: int
    ingest_run_id: int
    started_at: datetime
    completed_at: datetime
    database_url: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class CoinGeckoAssetPlatformsIngestResult(BaseModel):
    source: str
    status: str
    platform_filter: str | None = None
    fetched_count: int
    upserted_count: int
    ingest_run_id: int
    started_at: datetime
    completed_at: datetime
    database_url: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class CoinGeckoNftsListIngestResult(BaseModel):
    source: str
    status: str
    order: str | None = None
    per_page: int
    pages_fetched: int
    fetched_count: int
    upserted_count: int
    ingest_run_id: int
    started_at: datetime
    completed_at: datetime
    database_url: str
    metadata: dict[str, Any] = Field(default_factory=dict)
