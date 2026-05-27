# Agent Scheduler

### Schedule OpenCode, Claude, Codex, and future headless agent harnesses with Prefect

**Prompt templates · Postgres-backed schedules · pluggable runners**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.12%2B-blue.svg)](https://www.python.org/)
[![Prefect](https://img.shields.io/badge/Prefect-3.x-blueviolet.svg)](https://www.prefect.io/)
[![OpenCode](https://img.shields.io/badge/opencode-default-brightgreen.svg)](#supported-runners)
[![Claude](https://img.shields.io/badge/claude-supported-orange.svg)](#supported-runners)
[![Codex](https://img.shields.io/badge/codex-supported-blueviolet.svg)](#supported-runners)

Agent Scheduler is a standalone scheduler for headless agent workflows. It stores typed workflow parameters in Prefect, renders a prompt when the schedule fires, and passes that prompt to a selected agent harness.

OpenCode is the primary default runner. Claude and Codex are supported alternatives. The runner layer is intentionally isolated so more harnesses can be added without changing schedule storage, Prefect deployment logic, or workflow definitions.

For AI agents and automation harnesses, start with [COMMAND_INDEX.md](COMMAND_INDEX.md). It lists all CLI commands, Make targets, payload templates, runner options, response shapes, and end-to-end usage flows.

## Why Agent Scheduler?

Headless agents are useful for recurring operational work, but scheduling them directly creates a few hard problems:

- prompts need to be parameterized and changed without code deploys
- scheduled runs need durable state, retries, logs, and visibility
- multiple agent harnesses should share one scheduling layer
- the real skill artifact and the scheduler completion signal need to stay separate

Agent Scheduler uses Prefect for orchestration and Postgres-backed state while keeping the public CLI focused on registered agent workflows, not arbitrary command execution.

---

## Key Features

| | |
|---|---|
| **Prompt-template workflows** | Store prompt text plus variables in Prefect deployment parameters, then render the final prompt at run time. |
| **Pluggable runners** | OpenCode is default, Claude and Codex are supported, fake runner is available for tests. |
| **Postgres-backed orchestration** | Prefect stores deployments, schedules, run parameters, logs, and state in Postgres. |
| **Completion signals** | Workflows can require a small `.done.json` signal so Prefect can verify the agent finished. |
| **Skill-owned artifacts** | The agent skill owns the actual report/output format and path, such as markdown reports. |
| **Concurrency controls** | Default global and per-workflow concurrency limits prevent uncontrolled overlapping agent runs. |
| **Agent-safe CLI** | The CLI schedules registered workflows only; it does not expose arbitrary shell commands. |

---

## How It Works

```text
Prefect schedule fires
  -> Prefect worker starts agent-scheduler flow
  -> flow loads the registered workflow
  -> flow validates deployment parameters
  -> flow renders the final prompt
  -> runner adapter calls OpenCode, Claude, or Codex headless
  -> agent executes the skill or prompt
  -> agent writes skill artifacts according to the skill contract
  -> agent optionally writes a completion signal JSON
  -> Prefect records logs, status, retries, and result metadata
```

For the current stock market close summary workflow, the rendered prompt looks like:

```text
Run skill in examples/flows/market_close_summary for the following assets: GEMI, PLTR.

Market close date: 2026-05-26.

Generate the actual report exactly as defined by the skill instructions, including the output format and output path specified by the skill.

After the skill has produced its report, write a completion signal JSON file to outputs/daily-stock-market-close-summary.done.json with at least: {"status":"completed","assets":["GEMI","PLTR"],"market_close_date":"2026-05-26"}.
```

The markdown report is produced wherever the local example skill says to store it. The `.done.json` file is only the scheduler completion signal.

---

## Permission Model

Agent Scheduler orchestrates runs; the selected agent harness performs the work. A scheduled agent can only use the capabilities available to the worker process that launched it.

Typical permission boundaries:

| Boundary | Examples |
|---|---|
| Filesystem | Workspace files, output folders, mounted volumes. |
| Network | Public APIs, private APIs, package registries, internal services. |
| Installed tools | `opencode`, `claude`, `codex`, `psql`, project CLIs, data tools. |
| Environment secrets | Database URLs, API keys, exchange credentials, cloud tokens. |
| Database roles | Read-only analytics, public dataset writer, private trading writer. |

This means the system is intentionally broad but permission-scoped. If a worker has `PIPELINE_DATABASE_URL`, an agent can write public pipeline data. If a worker has private exchange credentials, an agent may be able to perform private trading actions. Production deployments should pass only the secrets and tools needed by that specific workflow.

For direct DB-writing prompts, the prompt must specify the database URL env var, schema, table, columns, and insert/upsert behavior. Example:

```text
Get current local weather for Singapore.

Store the result using PIPELINE_DATABASE_URL.
Use table public_data.weather_observations.
Create the table if it does not exist.
Insert one row with observed_at, location, temperature_c, condition, humidity_percent, source, raw_payload, and created_at.
After the insert succeeds, print a JSON summary with status and inserted row count.
```

For repeatable production pipelines, prefer a repo-owned command or script with tested schema handling:

```text
Run `agent-scheduler pipeline ingest-weather --location Singapore` and report whether it succeeded.
```

That keeps schema creation, validation, migrations, and credentials inside code rather than relying on prompt-generated SQL.

---

## Supported Runners

| Runner | Status | Purpose |
|---|---|---|
| `opencode` | Default | Primary local headless agent harness. |
| `claude` | Supported | Alternative Claude Code headless agent harness. |
| `codex` | Supported | Alternative headless agent harness. |
| `fake` | Test-only | Validates payloads and prompt rendering without invoking a real agent. |

OpenCode, Claude, and Codex must be installed in the runtime that starts the worker. For local development, use a host worker.

Default OpenCode worker:

```bash
make worker-opencode
```

Claude worker:

```bash
make worker-claude
```

The Docker worker is available for containerized deployments, but it needs the selected agent CLI installed inside the image.

---

## Step-By-Step Setup

### 1. Install prerequisites

Required:

- Python 3.12+
- `uv`
- Docker and Docker Compose
- OpenCode for the default runner

Claude and Codex are optional and used only when a payload selects `"runner": "claude"` or `"runner": "codex"`.

Install `uv`:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
uv --version
```

Install and verify Docker:

```bash
docker --version
docker compose version
```

Install and verify OpenCode for the default runner:

```bash
curl -fsSL https://opencode.ai/install | bash
opencode --version
```

If you prefer npm and already have Node.js installed:

```bash
npm install -g opencode-ai@latest
opencode --version
```

Install and verify Codex if you want to run payloads with `"runner": "codex"`:

```bash
npm install -g @openai/codex
codex --version
```

Install and verify Claude Code if you want to run payloads with `"runner": "claude"`:

```bash
npm install -g @anthropic-ai/claude-code
claude --version
```

The selected agent CLI must be installed in the same runtime that starts the Prefect worker. For local development, that usually means installing OpenCode, Claude, or Codex on the host and running:

```bash
make worker-opencode
```

For Claude-specific worker naming:

```bash
make worker-claude
```

### 2. Create local environment files

Copy the example env file for local development:

```bash
cp .env.example .env.local
```

Then review `.env.local`. At minimum, local development expects:

```text
PREFECT_API_URL=http://127.0.0.1:4200/api
PREFECT_API_DATABASE_CONNECTION_URL=postgresql+asyncpg://prefect:prefect@postgres:5432/prefect
AGENT_SCHEDULER_DATABASE_URL=postgresql+asyncpg://agent_scheduler_app:agent_scheduler@postgres:5432/agent_scheduler
PIPELINE_DATABASE_URL=postgresql+asyncpg://pipeline_app:pipeline_app@postgres:5432/pipeline_data
TRADING_PRIVATE_DATABASE_URL=postgresql+asyncpg://trading_private_writer:trading_private@postgres:5432/pipeline_data
```

For Docker bootstrap, the local Postgres container should start with the admin database defaults, then the init script creates the app databases and users:

```text
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=postgres

PREFECT_DB_NAME=prefect
PREFECT_DB_USER=prefect
PREFECT_DB_PASSWORD=prefect
AGENT_SCHEDULER_DB_NAME=agent_scheduler
AGENT_SCHEDULER_DB_USER=agent_scheduler_app
AGENT_SCHEDULER_DB_PASSWORD=agent_scheduler
PIPELINE_DB_NAME=pipeline_data
PIPELINE_DB_USER=pipeline_app
PIPELINE_DB_PASSWORD=pipeline_app
TRADING_PRIVATE_DB_USER=trading_private_writer
TRADING_PRIVATE_DB_PASSWORD=trading_private
ANALYTICS_DB_USER=analytics_reader
ANALYTICS_DB_PASSWORD=analytics_reader
```

Real `.env.local`, `.env.dev`, and `.env.prod` files are gitignored.

### 3. Create the virtual environment

```bash
make setup
```

### 4. Run tests

```bash
make test
```

### 5. Validate a payload without Prefect or a real agent

```bash
make test-stock-market-close-summary
```

This uses the fake runner and prints the rendered prompt context as JSON.

### 6. Start Prefect and Postgres

```bash
make services-up
make services-ps
```

Prefect UI runs at:

```text
http://127.0.0.1:4200
```

On a fresh Postgres volume, startup creates separate databases for Prefect orchestration, scheduler app metadata, and pipeline datasets. To smoke-check application database access:

```bash
make db-check-access
```

If the local Postgres volume was created before the separated database layout, apply the idempotent bootstrap once before checking access:

```bash
make db-bootstrap-existing
make db-check-access
```

### 7. Start a worker

For local OpenCode runs, start a host worker because OpenCode is installed on the host:

```bash
make worker-opencode
```

For Claude runs, use the Claude worker instead:

```bash
make worker-claude
```

Keep this terminal open.

### 8. Deploy and run the stock market close summary flow

```bash
make flow-stock-market-close-summary-deploy
make flow-stock-market-close-summary-run
```

### 9. Inspect outputs

Prefect stores run metadata, parameters, state, and logs in Postgres. Generated artifacts live in `outputs/`.

```bash
find outputs -maxdepth 4 -type f -print
cat outputs/daily-stock-market-close-summary.done.json
cat outputs/market-close-summary/2026-05-26/summary.md
```

The `.done.json` file is the scheduler completion signal. The markdown report is the skill-owned artifact.

---

## CLI Usage

External harnesses integrate through JSON payloads and CLI calls. The contract is:

1. Write a schedule payload JSON.
2. Call `agent-scheduler deploy` or `agent-scheduler schedule create`.
3. Parse the JSON response.
4. Use `run-now`, `schedule pause`, `schedule resume`, or `schedule delete` for operations.

### Payload Contract

```json
{
  "name": "daily-stock-market-close-summary",
  "task": "run_prompt",
  "runner": "opencode",
  "schedule": {
    "type": "cron",
    "cron": "0 16 * * *",
    "timezone": "Asia/Singapore"
  },
  "params": {
    "prompt": "Run skill in {skill_path} for the following assets: {assets}.",
    "variables": {
      "skill_path": "examples/flows/market_close_summary",
      "assets": ["GEMI", "PLTR"]
    },
    "completion_signal_path": "outputs/daily-stock-market-close-summary.done.json"
  },
  "work_pool_name": "agent-scheduler"
}
```

Fields:

| Field | Purpose |
|---|---|
| `name` | Prefect deployment name. Use a stable name; deploy is an upsert. |
| `task` / `workflow_name` | Registered scheduler workflow. Use `run_prompt` for generic prompt scheduling. |
| `runner` | Optional. Use `opencode`, `claude`, or `codex`; omitted means workflow default, currently `opencode`. |
| `schedule` | Cron or one-shot schedule with explicit timezone. |
| `params.prompt` | Prompt template passed to the runner after variable rendering. |
| `params.variables` | Values used in `{placeholder}` prompt rendering. Lists render as comma-separated text. |
| `params.completion_signal_path` | Optional JSON signal file path verified after real runner completion. |
| `work_pool_name` | Prefect work pool. Defaults to `agent-scheduler`. |

One-shot schedule shape:

```json
{
  "type": "once",
  "run_at": "2026-05-27T16:00:00+07:00",
  "timezone": "Asia/Singapore"
}
```

### Validate A Payload

Use the fake runner before deploying:

```bash
uv run agent-scheduler run-now \
  --payload examples/stock_market_close_summary_daily.json \
  --fake
```

Expected response shape:

```json
{"ok": true, "result": {"runner": "fake", "status": "succeeded"}}
```

### Deploy Or Update A Schedule

```bash
uv run agent-scheduler deploy examples/stock_market_close_summary_daily.json
```

Equivalent schedule namespace:

```bash
uv run agent-scheduler schedule create examples/stock_market_close_summary_daily.json
uv run agent-scheduler schedule update examples/stock_market_close_summary_daily.json
```

`deploy`, `schedule create`, and `schedule update` all write through the Prefect API. Do not edit Prefect Postgres tables directly.

### Run Immediately

Run directly from a payload:

```bash
uv run agent-scheduler run-now \
  --payload examples/stock_market_close_summary_daily.json
```

Run from a deployed schedule:

```bash
uv run agent-scheduler run-now \
  --deployment agent-scheduler-run-workflow/daily-stock-market-close-summary
```

### List And Inspect Schedules

```bash
uv run agent-scheduler schedule list

uv run agent-scheduler schedule inspect \
  agent-scheduler-run-workflow/daily-stock-market-close-summary
```

### Pause And Resume

```bash
uv run agent-scheduler schedule pause \
  agent-scheduler-run-workflow/daily-stock-market-close-summary

uv run agent-scheduler schedule resume \
  agent-scheduler-run-workflow/daily-stock-market-close-summary
```

### Delete

```bash
uv run agent-scheduler schedule delete \
  agent-scheduler-run-workflow/daily-stock-market-close-summary
```

### Use Claude Or Codex Instead Of OpenCode

Set the payload runner:

```json
{
  "runner": "claude"
}
```

or:

```json
{
  "runner": "codex"
}
```

The worker runtime must have the selected `claude` or `codex` CLI installed. For Claude, start a host worker with:

```bash
make worker-claude
```

The Claude runner invokes Claude Code in headless print mode and expects `claude` to be available on `PATH`.

### Environment Selection

Most CLI commands accept `--env`:

```bash
uv run agent-scheduler deploy examples/stock_market_close_summary_daily.json --env dev
uv run agent-scheduler schedule list --env prod
```

This loads `.env.dev` or `.env.prod`.

### JSON Responses

Successful commands return:

```json
{"ok": true}
```

Failures return nonzero exit codes with:

```json
{"ok": false, "error": {"code": "invalid_payload", "message": "..."}}
```

Harnesses should parse `ok` and `error.code` rather than scraping logs.

### Make Targets

Common Make targets:

```bash
make setup                  # Create .venv and install dependencies with uv
make test                   # Run pytest
make services-up            # Start Postgres and Prefect server
make services-down          # Stop local services
make services-logs          # Tail service logs
make db-bootstrap-existing  # Apply DB bootstrap to an existing local Postgres volume
make db-check-access        # Smoke-check scheduler, public pipeline, and private trading DB access
make worker-opencode        # Start host process worker for OpenCode
make worker-claude          # Start host process worker for Claude
make worker                 # Start generic host process worker
make test-stock-market-close-summary            # Render and run stock close payload with fake runner
make flow-stock-market-close-summary-deploy     # Deploy/update stock close Prefect deployment
make flow-stock-market-close-summary-run        # Trigger stock close deployment immediately
make smoke-run-fake         # Run simple smoke payload with fake runner
make smoke-deploy           # Deploy simple smoke workflow
make smoke-run-deployment   # Trigger smoke deployment immediately
```

Direct CLI examples:

```bash
uv run agent-scheduler --help
uv run agent-scheduler run-now --payload examples/stock_market_close_summary_daily.json --fake
uv run agent-scheduler deploy examples/stock_market_close_summary_daily.json
uv run agent-scheduler run-now --deployment agent-scheduler-run-workflow/daily-stock-market-close-summary
```

---

## Configuration

Environment files are used for credentials and runtime settings:

```text
.env.local
.env.dev
.env.prod
```

Use `.env.example` as the template. Real env files are gitignored.

Important settings:

| Setting | Purpose |
|---|---|
| `PREFECT_API_URL` | Prefect API endpoint used by local CLI and workers. |
| `PREFECT_API_DATABASE_CONNECTION_URL` | Postgres connection URL used only by the Prefect server. |
| `AGENT_SCHEDULER_DATABASE_URL` | Scheduler application metadata database URL. |
| `PIPELINE_DATABASE_URL` | General pipeline/public dataset database URL. |
| `TRADING_PRIVATE_DATABASE_URL` | Private trading dataset writer database URL. |
| `POSTGRES_USER` / `POSTGRES_PASSWORD` / `POSTGRES_DB` | Local Postgres bootstrap admin credentials. Defaults are `postgres/postgres/postgres`. |
| `AGENT_SCHEDULER_GLOBAL_CONCURRENCY` | Global concurrent agent run limit. |
| `OPENCODE_WORKER_NAME` | Name used by the OpenCode worker. |
| `CLAUDE_WORKER_NAME` | Name used by the Claude worker. |

Prefect Variables may be used for non-secret shared defaults. Credentials should live in env files or Prefect secrets, not in Prefect Variables.

### Database Boundaries

The local Postgres container is initialized with separate database ownership boundaries:

| Database | Schema | Owner / Writer | Purpose |
|---|---|---|---|
| `prefect` | Prefect-managed | `prefect` | Prefect orchestration tables only. |
| `agent_scheduler` | `scheduler_app` | `agent_scheduler_app` | Scheduler metadata, audit events, artifact indexes, and runner telemetry. |
| `pipeline_data` | `pipeline_app` | `pipeline_app` | Pipeline events, dataset versions, and source API logs. |
| `pipeline_data` | `public_data` | `pipeline_app` | Public external datasets such as CoinGecko or CoinMarketCap data. |
| `pipeline_data` | `trading_private` | `trading_private_writer` | Orderbooks, executions, balances, positions, and account snapshots. |

Postgres init scripts run only when Docker creates a new Postgres volume. If an existing local volume was created before this layout, create a new volume intentionally before expecting these databases and schemas to exist.

---

## Project Layout

```text
src/agent_scheduler/
  cli/              # Agent-facing CLI commands and JSON output
  config/           # Settings and env loading
  registry/         # Registered workflows and prompt rendering
  runners/          # OpenCode, Claude, Codex, fake runner adapters
  flows/            # Prefect flow and deployment helpers
  schedules/        # Schedule payload types and lifecycle helpers
  concurrency/      # Runtime concurrency keys and limits
pipelines/          # Repository-owned custom Prefect pipeline scripts
examples/           # Example deployment payloads
examples/flows/     # Repo-local example agent flows/skills
docs/               # Plan and workflow docs
tests/              # Unit and integration-style tests
```

---

## Development Status

This project is in active initial development.

Implemented:

- Python 3.12 + `uv` project scaffold
- Prefect + Postgres local runtime
- workflow registry
- OpenCode, Claude, Codex, and fake runner adapters
- generic `run_prompt` workflow
- deployment and run-now CLI paths
- stock market close summary payload
- completion signal verification

Planned:

- richer deployment parameter update commands
- backfill helper commands
- broader integration tests against the local Prefect/Postgres stack
- additional runner adapters

---

## License

MIT. See [LICENSE](LICENSE).
