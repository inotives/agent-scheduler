import json

from agent_scheduler.pipelines.coingecko.client import (
    CoinGeckoClient,
    CoinGeckoClientConfig,
)


class FakeResponse:
    payload = [{"id": "bitcoin", "symbol": "btc", "name": "Bitcoin"}]

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        return None

    def read(self) -> bytes:
        return json.dumps(self.payload).encode()


def test_coingecko_client_builds_expected_request(monkeypatch) -> None:
    calls = []

    def fake_urlopen(request, timeout):
        calls.append((request, timeout))
        return FakeResponse()

    monkeypatch.setattr("agent_scheduler.pipelines.coingecko.client.urlopen", fake_urlopen)

    client = CoinGeckoClient(
        CoinGeckoClientConfig(
            base_url="https://example.test/api/v3",
            api_key="secret",
            timeout_seconds=5,
        )
    )

    payload = client.get_coins_list(include_platform=True, status="inactive")

    request, timeout = calls[0]
    assert payload[0]["id"] == "bitcoin"
    assert timeout == 5
    assert request.full_url == (
        "https://example.test/api/v3/coins/list?include_platform=true&status=inactive"
    )
    assert request.headers["X-cg-pro-api-key"] == "secret"


def test_coingecko_client_builds_asset_platforms_request(monkeypatch) -> None:
    calls = []
    response = FakeResponse()
    response.payload = [{"id": "polygon-pos", "name": "Polygon POS"}]

    def fake_urlopen(request, timeout):
        calls.append((request, timeout))
        return response

    monkeypatch.setattr("agent_scheduler.pipelines.coingecko.client.urlopen", fake_urlopen)

    client = CoinGeckoClient(
        CoinGeckoClientConfig(base_url="https://example.test/api/v3", timeout_seconds=5)
    )

    payload = client.get_asset_platforms(filter_value="nft")

    request, timeout = calls[0]
    assert payload[0]["id"] == "polygon-pos"
    assert timeout == 5
    assert request.full_url == "https://example.test/api/v3/asset_platforms?filter=nft"


def test_coingecko_client_builds_nfts_list_request(monkeypatch) -> None:
    calls = []
    response = FakeResponse()
    response.payload = [{"id": "bored-ape-yacht-club", "name": "Bored Ape Yacht Club"}]

    def fake_urlopen(request, timeout):
        calls.append((request, timeout))
        return response

    monkeypatch.setattr("agent_scheduler.pipelines.coingecko.client.urlopen", fake_urlopen)

    client = CoinGeckoClient(
        CoinGeckoClientConfig(base_url="https://example.test/api/v3", timeout_seconds=5)
    )

    payload = client.get_nfts_list(order="market_cap_usd_desc", per_page=250, page=2)

    request, timeout = calls[0]
    assert payload[0]["id"] == "bored-ape-yacht-club"
    assert timeout == 5
    assert request.full_url == (
        "https://example.test/api/v3/nfts/list?"
        "per_page=250&page=2&order=market_cap_usd_desc"
    )
