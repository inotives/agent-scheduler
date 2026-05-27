from __future__ import annotations

import argparse
import asyncio
import json

from pydantic import ValidationError

from agent_scheduler.config.settings import load_settings
from agent_scheduler.pipelines.coingecko.asset_platforms import ingest_asset_platforms
from agent_scheduler.pipelines.coingecko.client import CoinGeckoClientConfig


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest CoinGecko asset platforms.")
    parser.add_argument("--filter", choices=["nft"], dest="platform_filter")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--env")
    args = parser.parse_args()

    try:
        settings = load_settings(env=args.env)
        result = asyncio.run(
            ingest_asset_platforms(
                database_url=settings.pipeline_database_url,
                client_config=CoinGeckoClientConfig(
                    base_url=settings.coingecko_api_base_url,
                    api_key=settings.coingecko_api_key,
                    api_key_header=settings.coingecko_api_key_header,
                    timeout_seconds=settings.coingecko_request_timeout_seconds,
                ),
                platform_filter=args.platform_filter,
                dry_run=args.dry_run,
            )
        )
    except ValidationError as exc:
        print(
            json.dumps(
                {
                    "ok": False,
                    "error": {
                        "code": "invalid_config",
                        "message": "Configuration validation failed.",
                        "details": exc.errors(include_url=False),
                    },
                }
            )
        )
        raise SystemExit(1) from exc
    except Exception as exc:
        print(
            json.dumps(
                {
                    "ok": False,
                    "error": {"code": "pipeline_failed", "message": str(exc)},
                }
            )
        )
        raise SystemExit(1) from exc

    print(json.dumps({"ok": True, "result": result.model_dump(mode="json")}))


if __name__ == "__main__":
    main()
