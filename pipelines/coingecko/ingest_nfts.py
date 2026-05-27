from __future__ import annotations

import argparse
import asyncio
import json

from pydantic import ValidationError

from agent_scheduler.config.settings import load_settings
from agent_scheduler.pipelines.coingecko.client import CoinGeckoClientConfig
from agent_scheduler.pipelines.coingecko.nfts_list import ingest_nfts_list


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest CoinGecko NFT collection list.")
    parser.add_argument("--order")
    parser.add_argument("--per-page", type=int, default=250)
    parser.add_argument("--max-pages", type=int)
    parser.add_argument("--request-delay-seconds", type=float)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--env")
    args = parser.parse_args()

    try:
        settings = load_settings(env=args.env)
        result = asyncio.run(
            ingest_nfts_list(
                database_url=settings.pipeline_database_url,
                client_config=CoinGeckoClientConfig(
                    base_url=settings.coingecko_api_base_url,
                    api_key=settings.coingecko_api_key,
                    api_key_header=settings.coingecko_api_key_header,
                    timeout_seconds=settings.coingecko_request_timeout_seconds,
                ),
                order=args.order,
                per_page=args.per_page,
                max_pages=args.max_pages,
                request_delay_seconds=(
                    args.request_delay_seconds
                    if args.request_delay_seconds is not None
                    else settings.coingecko_paginated_request_delay_seconds
                ),
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
