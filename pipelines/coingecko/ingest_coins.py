from __future__ import annotations

import argparse
import asyncio
import json

from pydantic import ValidationError

from agent_scheduler.config.settings import load_settings
from agent_scheduler.pipelines.coingecko.client import CoinGeckoClientConfig
from agent_scheduler.pipelines.coingecko.coins_list import ingest_coins_list


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest CoinGecko coin list.")
    parser.add_argument("--include-platform", action="store_true")
    parser.add_argument("--coin-status", choices=["active", "inactive"], default="active")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--env")
    args = parser.parse_args()

    try:
        settings = load_settings(env=args.env)
        result = asyncio.run(
            ingest_coins_list(
                database_url=settings.pipeline_database_url,
                client_config=CoinGeckoClientConfig(
                    base_url=settings.coingecko_api_base_url,
                    api_key=settings.coingecko_api_key,
                    api_key_header=settings.coingecko_api_key_header,
                    timeout_seconds=settings.coingecko_request_timeout_seconds,
                ),
                include_platform=args.include_platform,
                coin_status=args.coin_status,
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
