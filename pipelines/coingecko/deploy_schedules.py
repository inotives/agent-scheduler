from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from prefect.schedules import Cron

from agent_scheduler.flows.deployments import ensure_work_pool
from agent_scheduler.pipelines.coingecko.flows import (
    coingecko_ingest_asset_platforms_flow,
    coingecko_ingest_coins_flow,
    coingecko_ingest_nfts_list_flow,
)


WEEKLY_SUNDAY_10AM_CRON = "0 10 * * 0"
DEFAULT_TIMEZONE = "Asia/Singapore"
DEFAULT_WORK_POOL = "agent-scheduler"


def main() -> None:
    parser = argparse.ArgumentParser(description="Deploy CoinGecko pipeline schedules.")
    parser.add_argument("--work-pool-name", default=DEFAULT_WORK_POOL)
    parser.add_argument("--timezone", default=DEFAULT_TIMEZONE)
    parser.add_argument("--paused", action="store_true")
    args = parser.parse_args()

    ensure_work_pool(args.work_pool_name)
    schedule = Cron(WEEKLY_SUNDAY_10AM_CRON, timezone=args.timezone)
    working_dir = str(Path.cwd())
    job_variables = {"working_dir": working_dir}
    pipeline_database_url = os.getenv("PIPELINE_DATABASE_URL")
    if pipeline_database_url:
        job_variables["env"] = {"PIPELINE_DATABASE_URL": pipeline_database_url}

    coins_deployment = coingecko_ingest_coins_flow.to_deployment(
        name="weekly-coingecko-coins-list",
        work_pool_name=args.work_pool_name,
        schedule=schedule,
        paused=args.paused,
        parameters={"include_platform": True, "coin_status": "active"},
        job_variables=job_variables,
    )
    asset_platforms_deployment = coingecko_ingest_asset_platforms_flow.to_deployment(
        name="weekly-coingecko-asset-platforms",
        work_pool_name=args.work_pool_name,
        schedule=schedule,
        paused=args.paused,
        parameters={"platform_filter": None},
        job_variables=job_variables,
    )
    nfts_deployment = coingecko_ingest_nfts_list_flow.to_deployment(
        name="weekly-coingecko-nfts-list",
        work_pool_name=args.work_pool_name,
        schedule=schedule,
        paused=args.paused,
        parameters={"order": None, "per_page": 250, "max_pages": None},
        job_variables=job_variables,
    )

    coins_deployment_id = coins_deployment.apply(work_pool_name=args.work_pool_name)
    asset_platforms_deployment_id = asset_platforms_deployment.apply(
        work_pool_name=args.work_pool_name
    )
    nfts_deployment_id = nfts_deployment.apply(work_pool_name=args.work_pool_name)

    print(
        json.dumps(
            {
                "ok": True,
                "schedule": {
                    "cron": WEEKLY_SUNDAY_10AM_CRON,
                    "timezone": args.timezone,
                    "description": "Sunday 10:00:00",
                },
                "deployments": [
                    {
                        "name": "weekly-coingecko-coins-list",
                        "id": str(coins_deployment_id),
                    },
                    {
                        "name": "weekly-coingecko-asset-platforms",
                        "id": str(asset_platforms_deployment_id),
                    },
                    {
                        "name": "weekly-coingecko-nfts-list",
                        "id": str(nfts_deployment_id),
                    },
                ],
            }
        )
    )


if __name__ == "__main__":
    main()
