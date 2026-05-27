# Agent Scheduler Plan

## Summary

Build a new `uv` Python 3.12 project named `agent-scheduler` that exposes an agent-friendly CLI for scheduling headless agent tasks through Prefect. The system uses registered, typed Python task definitions, Prefect backed by Postgres as the orchestration/state backend, and pluggable runner adapters for OpenCode headless, Claude Code headless, Codex headless, and future agent CLIs.

Primary v1 use case: schedule a registered prompt-template workflow, such as running a skill from `<path_to_skill>` against an `<asset-list>` every day at `16:00:00`, using OpenCode, Claude Code, or Codex headless.

## Phase 1: Project Scaffold

Goal: create a clean, scalable Python project foundation.

- Create a `uv` Python 3.12 project with `pyproject.toml`, package metadata, lockfile, and CLI entry point `agent-scheduler`.
- Use a repo-local `.venv` created through `uv venv`; install and lock dependencies through `uv sync`.
- Add base dependencies for Prefect, Pydantic, env loading, testing, and a CLI framework.
- Add `.gitignore`, `.dockerignore`, and an environment template documenting required keys.
- Gitignore real `.env.local`, `.env.dev`, and `.env.prod` files.
- Add a `Makefile` as the canonical interface for setup, testing, local services, workers, and deployment commands.

Acceptance:

- `make setup` creates the local development environment.
- `make test` runs an empty or smoke test suite successfully.
- `agent-scheduler --help` runs through `uv`.

## Phase 2: Folder Structure and Configuration

Goal: establish boundaries that can scale across agent workflows, custom pipelines, and infrastructure.

```text
agent-scheduler/
  src/agent_scheduler/
    cli/              # Agent-facing CLI commands and JSON output contracts
    config/           # Settings, env loading, Prefect/Postgres connection config
    registry/         # Named agent workflow definitions and parameter models
    runners/          # Pluggable headless agent runner adapters
    flows/            # Prefect flows used by registered agent workflows
    schedules/        # Schedule parsing, upsert, pause/resume, delete helpers
    concurrency/      # Concurrency keys and run-overlap policy helpers
    logging/          # Prefect log bridging and structured run output helpers
  pipelines/          # Repository-owned custom Prefect pipeline scripts
  tests/
    unit/
    integration/
  infra/
    docker/
    prefect/
  docs/
  Makefile
  Dockerfile
  docker-compose.yml
  pyproject.toml
```

- Implement typed settings for env-specific configuration.
- Use `.env.local`, `.env.dev`, and `.env.prod` for credentials and deployment settings.
- Require `PREFECT_API_DATABASE_CONNECTION_URL` for the self-hosted Prefect server.
- Keep SQLite out of the project defaults.

Acceptance:

- Settings load from the selected env file.
- Missing required settings produce JSON-friendly CLI errors.
- The package imports cleanly from the `src/` layout.

## Phase 3: Docker, Postgres, and Prefect Runtime

Goal: run the orchestration stack locally in the same shape expected for deployment.

- Add a `Dockerfile` for the scheduler/worker runtime image.
- Add `docker-compose.yml` for Postgres, Prefect server, Prefect worker, and optional scheduler CLI/runtime container.
- Configure Prefect to use Postgres via `PREFECT_API_DATABASE_CONNECTION_URL`.
- Add Makefile targets for starting/stopping services, viewing logs, running migrations/setup, and starting a worker.
- Ensure Docker builds do not depend on the local `.venv`; local dev still uses `uv`.

Acceptance:

- `make services-up` starts Postgres and Prefect server.
- `make worker` starts a Prefect worker connected to the configured Prefect API.
- Prefect persists state in Postgres, not SQLite.

## Phase 4: Agent Workflow Registry

Goal: define a safe, typed contract for agentic scheduled work.

- Implement a Python registry of named workflows.
- Each workflow declares:
  - task name
  - Pydantic parameter model
  - allowed workspace
  - allowed runner type
  - retry, retry delay, timeout, and concurrency defaults
  - prompt rendering logic
- Keep the public CLI focused on agentic workflows only.
- Do not expose arbitrary command execution through the CLI.
- Allow repository-owned Python pipeline scripts in `pipelines/` to define custom Prefect flows outside the public agent CLI contract.

Acceptance:

- Unknown workflow names are rejected.
- Invalid params are rejected before Prefect execution.
- A registered workflow can render a deterministic prompt from typed params.

## Phase 5: Runner Adapters

Goal: invoke headless agents through a stable internal runner interface.

- Define a runner context JSON contract containing task name, validated params, workspace, Prefect run metadata, schedule/run IDs, attempt info, and rendered prompt.
- Implement runner adapters for:
  - Codex headless
  - Claude Code headless
  - OpenCode headless
  - fake/test runner
- Stream runner stdout/stderr into Prefect logs.
- Treat exit code `0` as success, nonzero exit as failure, and timeout as failed/cancelled according to task policy.
- Require workflows to write results to a predictable output path or emit a structured final JSON summary.

Acceptance:

- Fake runner can execute a workflow in tests without external agent CLIs.
- OpenCode/Claude/Codex command construction is isolated to runner adapters.
- Runner failures propagate to Prefect as failed runs.

## Phase 6: Prefect Flow and Scheduling Lifecycle

Goal: make registered workflows schedulable and manageable through Prefect.

- Implement the Prefect flow that:
  - loads the registered workflow
  - validates parameters
  - renders the final prompt
  - invokes the selected runner
  - records logs, status, retries, and result metadata
- Support cron and one-shot schedule types.
- Require explicit timezone for all schedule inputs.
- Use upsert-by-name behavior for schedules to avoid duplicate automation.
- Enforce default concurrency of one active run per task/workspace.
- Make global concurrent agent runs configurable, with default `2`.

Acceptance:

- A workflow can be deployed to Prefect.
- A cron schedule can be created or updated by name.
- A one-shot run can be scheduled.
- Overlapping runs for the same task/workspace are blocked or queued.

## Phase 7: Agent-Facing CLI

Goal: expose the minimum reliable interface agents need to operate the scheduler.

- Default all command output to stable JSON.
- Return nonzero exit codes on errors.
- Implement lifecycle commands:
  - deploy/register
  - schedule create/update
  - run now
  - list
  - inspect
  - pause
  - resume
  - delete
- Prefer Makefile targets over raw commands in documentation and operational workflows.

Acceptance:

- Agents can create/update a schedule using a JSON payload.
- Agents can inspect, pause, resume, and delete schedules.
- CLI errors are structured and machine-readable.

## Phase 8: First Workable Deployment

Goal: prove the end-to-end daily skill execution use case.

Implement the first registered workflow around a generic prompt template:

```text
<prompt text with optional {variables}>
```

Example schedule payload:

```json
{
  "task": "run_prompt",
  "schedule": {
    "type": "cron",
    "cron": "0 16 * * *",
    "timezone": "Asia/Singapore"
  },
  "params": {
    "prompt": "Run skill in {skill_path} for the following assets: {assets}. Market close date: {market_close_date}.",
    "variables": {
      "skill_path": "/path/to/skill",
      "assets": ["GEMI", "PLTR"],
      "market_close_date": "2026-05-26"
    }
  },
  "runner": "opencode"
}
```

Execution sequence:

```text
Prefect schedule triggers
  -> Prefect worker starts the flow
  -> flow loads the registered workflow
  -> flow validates parameters
  -> flow renders the final prompt
  -> flow invokes OpenCode/Claude/Codex headless
  -> agent executes until success, failure, or timeout
  -> Prefect records logs, status, retries, and result metadata
```

Acceptance:

- `make services-up` starts Postgres and Prefect.
- `make worker` starts the worker.
- `agent-scheduler deploy` registers the workflow.
- `agent-scheduler schedule ...` creates a daily 16:00 schedule with explicit timezone.
- `agent-scheduler run-now ...` executes the workflow through the fake runner in tests and a real runner in local development when installed.
- Prefect shows run history, logs, status, and failures.

## Fix Phase: Prompt Template Parameters

Goal: simplify scheduled agent work so Prefect passes a final prompt string to OpenCode/Claude/Codex.

- Add a generic `run_prompt` workflow as the primary scheduled workflow path.
- Store prompt templates and schedule-specific variables as Prefect deployment parameters.
- Render variables at flow runtime before invoking the selected runner.
- Render list variables as comma-separated text, e.g. `["GEMI", "PLTR"]` becomes `GEMI, PLTR`.
- Allow `run_prompt` to declare a completion signal JSON path that the flow verifies after a real runner exits.
- Keep skill-generated artifacts separate from scheduler completion signals; markdown output belongs to the skill contract.
- Keep `run_skill_for_assets` available as a compatibility workflow, but use `run_prompt` for the stock market close summary example.
- Use Prefect UI/API/CLI to update deployment parameters in Postgres; avoid direct SQL updates.
- Use ad-hoc flow runs with parameter overrides for historical backfills.

Acceptance:

- `run_prompt` accepts plain prompt text with optional variables.
- Missing prompt variables fail before invoking the runner.
- The stock market close summary payload schedules the skill for configured assets, with `GEMI` and `PLTR` as the default example assets for market close date `2026-05-26`.
- The stock market close summary payload asks the agent to write a completion signal JSON after the skill-generated markdown has been produced.

## Phase 9: Database Separation For Scheduler And Pipeline Data

Goal: keep orchestration state, scheduler application metadata, and custom pipeline datasets separated by database and schema boundaries.

Database layout:

```text
postgres
  database: prefect
    - Prefect-owned orchestration tables only

  database: agent_scheduler
    schema: scheduler_app
      - scheduler-owned metadata
      - run artifact index
      - completion signal mirror
      - workflow registry snapshots
      - deployment audit events
      - agent runner telemetry

  database: pipeline_data
    schema: pipeline_app
      - ingestion events
      - dataset versions
      - source API request logs

    schema: public_data
      - external public datasets
      - CoinGecko assets/prices
      - CoinMarketCap quotes
      - public market/reference snapshots

    schema: trading_private
      - orderbooks
      - trade executions
      - balances
      - positions
      - account snapshots
```

Configuration:

```env
PREFECT_API_DATABASE_CONNECTION_URL=postgresql+asyncpg://prefect:...@postgres:5432/prefect
AGENT_SCHEDULER_DATABASE_URL=postgresql+asyncpg://agent_scheduler_app:...@postgres:5432/agent_scheduler
PIPELINE_DATABASE_URL=postgresql+asyncpg://pipeline_app:...@postgres:5432/pipeline_data
TRADING_PRIVATE_DATABASE_URL=postgresql+asyncpg://trading_private_writer:...@postgres:5432/pipeline_data
```

Implementation tasks:

- Add Postgres init scripts under `infra/postgres/init/`.
- Create separate databases for `prefect`, `agent_scheduler`, and `pipeline_data`.
- Create separate users for Prefect, scheduler app metadata, general pipeline writes, trading-private writes, and read-only analytics.
- Create schemas `scheduler_app`, `pipeline_app`, `public_data`, and `trading_private`.
- Grant least-privilege access:
  - Prefect user only accesses the `prefect` database.
  - Scheduler app user accesses `agent_scheduler.scheduler_app`.
  - Pipeline app user writes `pipeline_data.pipeline_app` and `pipeline_data.public_data`.
  - Trading private writer writes `pipeline_data.trading_private` and may read `pipeline_data.public_data`.
  - Read-only analytics user may read `public_data` and selected `pipeline_app` tables, but not `trading_private`.
- Add typed settings for `AGENT_SCHEDULER_DATABASE_URL`, `PIPELINE_DATABASE_URL`, and `TRADING_PRIVATE_DATABASE_URL`.
- Keep custom pipeline datasets out of Prefect's internal database and out of scheduler app metadata tables.

Acceptance:

- `make services-up` initializes all required databases and schemas on a fresh Postgres volume.
- Prefect continues to use only the `prefect` database.
- Scheduler metadata has a distinct application database/schema.
- Public external datasets and private trading datasets are separated in `pipeline_data` schemas.
- Tests or smoke checks prove each configured user can access only its intended database/schema.

Implementation notes:

- Postgres bootstrap scripts live in `infra/postgres/init/`.
- `make db-check-access` smoke-checks writes for `scheduler_app`, `public_data`, and `trading_private`.
- Existing local Postgres volumes must be recreated intentionally before bootstrap scripts can create the new databases and schemas.

## Phase 10: Example Public Dataset Pipeline

Goal: prove the scheduler repo can also host deterministic custom pipelines without asking an agent prompt to invent schema or SQL at runtime.

Example pipeline:

```text
CoinGecko /coins/list
  -> fetch current coin ID map
  -> validate id, symbol, name, platforms
  -> create public_data tables when missing
  -> upsert into public_data.coingecko_coins
  -> record run metadata in public_data.pipeline_ingest_runs

CoinGecko /asset_platforms
  -> fetch current asset platform ID map
  -> validate id, chain_identifier, name, shortname, native_coin_id, image
  -> create public_data tables when missing
  -> upsert into public_data.coingecko_asset_platforms
  -> record run metadata in public_data.pipeline_ingest_runs

CoinGecko /nfts/list
  -> fetch paginated NFT collection ID map
  -> validate id, contract_address, name, asset_platform_id, symbol
  -> wait between paginated requests to avoid rate-limit pressure
  -> create public_data tables when missing
  -> upsert into public_data.coingecko_nft_collections
  -> record run metadata in public_data.pipeline_ingest_runs
```

Scalable structure:

```text
src/agent_scheduler/pipelines/
  common/           # shared DB and pipeline infrastructure
  coingecko/
    client.py       # source API client
    models.py       # validated API/result models
    repository.py   # target schema and persistence
    coins_list.py   # ingestion orchestration
    asset_platforms.py
    nfts_list.py

pipelines/coingecko/
  ingest_coins.py
  ingest_asset_platforms.py
  ingest_nfts.py
  README.md
```

Implementation tasks:

- Keep custom pipelines out of the agent-facing `agent-scheduler` CLI surface.
- Add reproducible scripts under `pipelines/coingecko/`.
- Use `PIPELINE_DATABASE_URL`, not Prefect's database and not `AGENT_SCHEDULER_DATABASE_URL`.
- Keep writes inside the `public_data` schema for public external datasets.
- Make schema creation idempotent.
- Add dry-run mode for fetch and validation without DB writes.
- Add Make targets for dry-run and real ingestion.
- Add weekly Prefect schedules for both CoinGecko datasets at Sunday `10:00:00` in `Asia/Singapore`.
- Document developer pipeline usage in README and `pipelines/coingecko/README.md`.

Acceptance:

- Dry-run can validate a CoinGecko response without database writes.
- Real ingestion creates or updates `public_data.coingecko_coins`.
- Real ingestion creates or updates `public_data.coingecko_asset_platforms`.
- Real ingestion creates or updates `public_data.coingecko_nft_collections`.
- Ingestion writes an audit record to `public_data.pipeline_ingest_runs`.
- Prefect deployments exist for `weekly-coingecko-coins-list`, `weekly-coingecko-asset-platforms`, and `weekly-coingecko-nfts-list` on cron `0 10 * * 0`.
- NFT ingestion uses an inter-page delay and supports `max_pages` for safe validation.
- Tests cover API client request construction, schema target names, and dry-run validation.

## Test Plan

- Unit test registry validation, unknown workflow rejection, parameter validation, workspace resolution, and prompt rendering.
- Unit test runner context construction and fake runner execution.
- Unit test schedule parsing for cron and one-shot inputs, including required timezone failures.
- Unit test JSON CLI output and error exit codes.
- Integration test with fake runner and Prefect/Postgres local stack for deploy, schedule upsert, run-now, list, inspect, pause/resume, and delete.
- Add a concurrency test proving overlapping runs for the same task/workspace are blocked or queued.

## Assumptions

- The first implementation is greenfield; the current repo only contains docs.
- CodeGraph should not be initialized during the initial implementation unless requested later.
- Local authorization is trusted: any local process that can run the CLI may schedule registered workflows.
- No separate API server or web UI is included in v1.
- Scheduler application metadata and custom pipeline datasets should be separated from Prefect orchestration state before adding persistent dataset ingestion.
- Prefect Cloud is out of scope for v1; self-hosted Prefect with Postgres is the expected deployment.
- Data/pipeline dependencies such as `pandas` or `polars` are added only when custom pipeline scripts require them; they are not base scheduler dependencies.
