from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen


@dataclass(frozen=True)
class CoinGeckoClientConfig:
    base_url: str = "https://api.coingecko.com/api/v3"
    api_key: str | None = None
    api_key_header: str = "x-cg-pro-api-key"
    timeout_seconds: float = 30.0


class CoinGeckoClient:
    def __init__(self, config: CoinGeckoClientConfig) -> None:
        self._config = config

    def get_coins_list(
        self,
        *,
        include_platform: bool = False,
        status: str = "active",
    ) -> list[dict[str, Any]]:
        query = urlencode(
            {
                "include_platform": str(include_platform).lower(),
                "status": status,
            }
        )
        url = f"{self._config.base_url.rstrip('/')}/coins/list?{query}"
        headers = {"accept": "application/json"}
        if self._config.api_key:
            headers[self._config.api_key_header] = self._config.api_key

        request = Request(url, headers=headers, method="GET")
        with urlopen(request, timeout=self._config.timeout_seconds) as response:
            payload = json.loads(response.read().decode("utf-8"))

        if not isinstance(payload, list):
            raise ValueError("CoinGecko coins list response must be a JSON array")
        return payload

    def get_asset_platforms(
        self,
        *,
        filter_value: str | None = None,
    ) -> list[dict[str, Any]]:
        query = urlencode({"filter": filter_value}) if filter_value else ""
        suffix = f"?{query}" if query else ""
        url = f"{self._config.base_url.rstrip('/')}/asset_platforms{suffix}"
        headers = {"accept": "application/json"}
        if self._config.api_key:
            headers[self._config.api_key_header] = self._config.api_key

        request = Request(url, headers=headers, method="GET")
        with urlopen(request, timeout=self._config.timeout_seconds) as response:
            payload = json.loads(response.read().decode("utf-8"))

        if not isinstance(payload, list):
            raise ValueError("CoinGecko asset platforms response must be a JSON array")
        return payload

    def get_nfts_list(
        self,
        *,
        order: str | None = None,
        per_page: int = 250,
        page: int = 1,
    ) -> list[dict[str, Any]]:
        query_values: dict[str, Any] = {"per_page": per_page, "page": page}
        if order:
            query_values["order"] = order
        query = urlencode(query_values)
        url = f"{self._config.base_url.rstrip('/')}/nfts/list?{query}"
        headers = {"accept": "application/json"}
        if self._config.api_key:
            headers[self._config.api_key_header] = self._config.api_key

        request = Request(url, headers=headers, method="GET")
        with urlopen(request, timeout=self._config.timeout_seconds) as response:
            payload = json.loads(response.read().decode("utf-8"))

        if not isinstance(payload, list):
            raise ValueError("CoinGecko NFTs list response must be a JSON array")
        return payload
