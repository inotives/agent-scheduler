# CoinGecko Public Dataset Pipelines

These examples ingest CoinGecko public reference datasets into the `public_data` schema.

## Layout

```text
src/agent_scheduler/pipelines/coingecko/
  client.py       # HTTP client for CoinGecko
  models.py       # validated API and result models
  repository.py   # Postgres schema and upsert logic
  coins_list.py   # orchestration function
  asset_platforms.py
  nfts_list.py

pipelines/coingecko/
  ingest_coins.py
  ingest_asset_platforms.py
  ingest_nfts.py
  README.md       # reproducible usage notes for this example
```

## Target Tables

The pipeline writes to the separate `pipeline_data` database using `PIPELINE_DATABASE_URL`.

Tables:

- `public_data.coingecko_coins`
- `public_data.coingecko_asset_platforms`
- `public_data.coingecko_nft_collections`
- `public_data.pipeline_ingest_runs`

`public_data.coingecko_coins` is upserted by CoinGecko coin `id`. It stores `symbol`, `name`, `platforms`, `status`, source metadata, and timestamps.

`public_data.coingecko_asset_platforms` is upserted by CoinGecko asset platform `id`. It stores `chain_identifier`, `name`, `shortname`, `native_coin_id`, `image`, source metadata, and timestamps.

`public_data.coingecko_nft_collections` is upserted by CoinGecko NFT collection `id`. It stores `contract_address`, `name`, `asset_platform_id`, `symbol`, source metadata, and timestamps.

## Run Locally

Start Postgres first:

```bash
make services-up
make db-check-access
```

Validate the API response without writing:

```bash
make pipeline-coingecko-coins-dry-run
```

Ingest the current active coin list:

```bash
make pipeline-coingecko-coins-ingest
```

Direct CLI equivalent:

```bash
PIPELINE_DATABASE_URL=postgresql+asyncpg://pipeline_app:pipeline_app@127.0.0.1:5432/pipeline_data \
  uv run python pipelines/coingecko/ingest_coins.py --include-platform
```

Inactive coins:

```bash
uv run python pipelines/coingecko/ingest_coins.py --coin-status inactive
```

Validate the asset platforms API response without writing:

```bash
make pipeline-coingecko-asset-platforms-dry-run
```

Ingest the asset platforms list:

```bash
make pipeline-coingecko-asset-platforms-ingest
```

NFT-supported asset platforms:

```bash
uv run python pipelines/coingecko/ingest_asset_platforms.py --filter nft
```

Validate the first NFT list page without writing:

```bash
make pipeline-coingecko-nfts-dry-run
```

Ingest all NFT list pages:

```bash
make pipeline-coingecko-nfts-ingest
```

The NFT endpoint is paginated. The script defaults to `per_page=250` and waits `COINGECKO_PAGINATED_REQUEST_DELAY_SECONDS` between pages. The default delay is 6 seconds, which keeps paginated ingestion conservative for public-plan rate limits. For ad-hoc validation, prefer `--max-pages 1`.

## Weekly Prefect Schedules

Deploy all CoinGecko pipelines to Prefect:

```bash
make pipeline-coingecko-deploy-schedules
```

Schedule:

```text
0 10 * * 0
timezone: Asia/Singapore
meaning: Sunday 10:00:00
```

Deployments:

| Deployment | Flow | Target |
|---|---|---|
| `weekly-coingecko-coins-list` | `coingecko-ingest-coins` | `public_data.coingecko_coins` |
| `weekly-coingecko-asset-platforms` | `coingecko-ingest-asset-platforms` | `public_data.coingecko_asset_platforms` |
| `weekly-coingecko-nfts-list` | `coingecko-ingest-nfts-list` | `public_data.coingecko_nft_collections` |

Trigger them manually after deploy:

```bash
make pipeline-coingecko-coins-run-deployment
make pipeline-coingecko-asset-platforms-run-deployment
make pipeline-coingecko-nfts-run-deployment
```

These deployments run as repo-owned Prefect flows. They are intentionally not exposed through the agent-facing `agent-scheduler` CLI.

## Environment

```text
PIPELINE_DATABASE_URL=postgresql+asyncpg://pipeline_app:pipeline_app@postgres:5432/pipeline_data
COINGECKO_API_BASE_URL=https://api.coingecko.com/api/v3
COINGECKO_API_KEY=
COINGECKO_API_KEY_HEADER=x-cg-pro-api-key
COINGECKO_REQUEST_TIMEOUT_SECONDS=30
COINGECKO_PAGINATED_REQUEST_DELAY_SECONDS=6
```

For paid CoinGecko plans, set `COINGECKO_API_BASE_URL` and `COINGECKO_API_KEY` according to the plan.
