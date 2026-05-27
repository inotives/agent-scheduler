# Agent Scheduler Command Index

This file is the integration reference for AI agents and automation harnesses. It lists the supported CLI commands, Make targets, payload templates, runner options, and response contracts.

## Integration Contract

Agent Scheduler is controlled through JSON payload files and JSON CLI responses.

Standard flow:

1. Create or update a payload JSON file.
2. Validate it with the fake runner.
3. Deploy it to Prefect.
4. Start a worker for the selected runner.
5. Trigger or let the schedule run.
6. Inspect Prefect logs and generated output files.

Use `uv run agent-scheduler ...` for direct CLI calls. Use `make ...` targets for common local workflows.

## Response Contract

Successful commands return JSON with `ok: true`:

```json
{"ok": true}
```

Failed commands return a nonzero exit code and JSON with `ok: false`:

```json
{
  "ok": false,
  "error": {
    "code": "invalid_payload",
    "message": "Payload validation failed.",
    "details": []
  }
}
```

Automation should parse `ok` and `error.code`. Do not scrape human logs for status.

## Runner Names

| Runner | Payload value | Notes |
|---|---|---|
| OpenCode | `"opencode"` | Default primary runner. Requires `opencode` in the worker runtime. |
| Claude Code | `"claude"` | Supported alternative. Requires `claude` in the worker runtime. |
| Codex | `"codex"` | Supported alternative. Requires `codex` in the worker runtime. |
| Fake | `--fake` CLI flag | Test-only direct execution; never stored as a payload runner. |

If `runner` is omitted, `run_prompt` defaults to `opencode`.

## Registered Workflows

| Workflow | Task name | Purpose |
|---|---|---|
| Prompt workflow | `run_prompt` | Generic scheduled prompt with optional variables and optional completion signal verification. |
| Agent smoke | `agent_smoke` | Minimal prompt smoke test. |
| Skill for assets | `run_skill_for_assets` | Compatibility workflow for path + assets prompts. Prefer `run_prompt` for new schedules. |

## Payload Schema

Top-level schedule payload:

```json
{
  "name": "stable-deployment-name",
  "task": "run_prompt",
  "runner": "opencode",
  "schedule": {
    "type": "cron",
    "cron": "0 16 * * *",
    "timezone": "Asia/Singapore"
  },
  "params": {},
  "work_pool_name": "agent-scheduler",
  "work_queue_name": null,
  "paused": false
}
```

Fields:

| Field | Required | Description |
|---|---:|---|
| `name` | yes | Prefect deployment name. Stable names are upserted. |
| `task` | yes | Registered workflow name. Alias for `workflow_name`. |
| `workflow_name` | no | Alternative to `task`. |
| `runner` | no | `opencode`, `claude`, or `codex`. Defaults to workflow default. |
| `schedule` | yes | Cron or one-shot schedule. |
| `params` | yes | Workflow-specific parameters. |
| `work_pool_name` | no | Defaults to `agent-scheduler`. |
| `work_queue_name` | no | Optional Prefect work queue. |
| `paused` | no | Whether deployment starts paused. Defaults to `false`. |

## Schedule Templates

Cron schedule:

```json
{
  "type": "cron",
  "cron": "0 16 * * *",
  "timezone": "Asia/Singapore"
}
```

One-shot schedule:

```json
{
  "type": "once",
  "run_at": "2026-05-27T16:00:00+07:00",
  "timezone": "Asia/Singapore"
}
```

Always include an explicit timezone.

## `run_prompt` Template

Use this for new scheduled agent work:

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
    "prompt": "Run skill in {skill_path} for the following assets: {assets}. Market close date: {market_close_date}.",
    "variables": {
      "skill_path": "examples/flows/market_close_summary",
      "assets": ["GEMI", "PLTR"],
      "market_close_date": "2026-05-26"
    },
    "completion_signal_path": "outputs/daily-stock-market-close-summary.done.json"
  },
  "work_pool_name": "agent-scheduler"
}
```

`variables` rendering rules:

- String, number, and boolean values render with `str(value)`.
- List values render as comma-separated text.
- `null` renders as an empty string.
- Missing placeholders fail before the runner is invoked.
- Use doubled braces for literal JSON braces in prompts: `{{"status":"completed"}}`.

Completion signal:

- Optional.
- If set, real runner executions must write a fresh JSON file at that path.
- Signal JSON must contain a successful status: `completed`, `succeeded`, or `success`.
- Fake runner skips completion signal verification.

Completion signal example:

```json
{
  "status": "completed",
  "assets": ["GEMI", "PLTR"],
  "market_close_date": "2026-05-26"
}
```

## Stock Market Close Summary Payload

Canonical example payload:

```text
examples/stock_market_close_summary_daily.json
```

Local example skill:

```text
examples/flows/market_close_summary/SKILL.md
```

Expected scheduler completion signal:

```text
outputs/daily-stock-market-close-summary.done.json
```

Expected skill-owned markdown artifact:

```text
outputs/market-close-summary/2026-05-26/summary.md
```

## Direct CLI Commands

### Root Help

```bash
uv run agent-scheduler --help
```

Purpose: list top-level commands.

### Health

```bash
uv run agent-scheduler health
```

Purpose: verify CLI process is callable.

Typical response:

```json
{"status": "ok"}
```

### Config Check

```bash
uv run agent-scheduler config check
uv run agent-scheduler config check --env dev
uv run agent-scheduler config check --env prod
```

Purpose: validate selected `.env` configuration.

Required database URLs:

| Variable | Boundary |
|---|---|
| `PREFECT_API_DATABASE_CONNECTION_URL` | Prefect orchestration database only. |
| `AGENT_SCHEDULER_DATABASE_URL` | Scheduler metadata database, `scheduler_app` schema. |
| `PIPELINE_DATABASE_URL` | General pipeline and public dataset database, `pipeline_app` and `public_data` schemas. |
| `TRADING_PRIVATE_DATABASE_URL` | Private trading dataset writer, `trading_private` schema. |

Optional public pipeline settings:

| Variable | Purpose |
|---|---|
| `COINGECKO_API_BASE_URL` | CoinGecko API base URL. Defaults to `https://api.coingecko.com/api/v3`. |
| `COINGECKO_API_KEY` | Optional CoinGecko API key. |
| `COINGECKO_API_KEY_HEADER` | Header used for API key auth. Defaults to `x-cg-pro-api-key`. |
| `COINGECKO_REQUEST_TIMEOUT_SECONDS` | Request timeout for CoinGecko API calls. |

### Validate Payload With Fake Runner

```bash
uv run agent-scheduler run-now \
  --payload examples/stock_market_close_summary_daily.json \
  --fake
```

Purpose: validate payload, render prompt, and return fake runner context without Prefect or a real agent.

Use this before deploy.

### Run Payload Directly With Real Runner

```bash
uv run agent-scheduler run-now \
  --payload examples/stock_market_close_summary_daily.json
```

Purpose: execute the payload immediately in the current process using its selected real runner.

Requirements:

- selected runner CLI installed locally
- completion signal written if `completion_signal_path` is set

### Backfill Historical Payload

```bash
uv run agent-scheduler backfill run examples/stock_market_close_summary_daily.json \
  --var market_close_date=2026-05-20 \
  --asset GEMI \
  --asset PLTR \
  --set completion_signal_path=outputs/backfill-stock-market-close-summary-2026-05-20.done.json
```

Purpose: execute a payload once with temporary overrides. This does not update the JSON file or the Prefect deployment.

Validation mode:

```bash
uv run agent-scheduler backfill run examples/stock_market_close_summary_daily.json \
  --fake \
  --var market_close_date=2026-05-20 \
  --asset GEMI \
  --asset PLTR
```

Options:

| Option | Description |
|---|---|
| `--var key=value` | Override `params.variables[key]`. Use for `run_prompt` placeholders. |
| `--asset SYMBOL` | Replace `params.variables.assets`; also sets `assets_json` to a JSON array string. Repeat for multiple assets. |
| `--set key=value` | Override top-level `params[key]`, such as `completion_signal_path`. |
| `--runner opencode|claude|codex` | Override runner for this run only. |
| `--fake` | Validate and render without invoking a real runner. |
| `--env local|dev|prod` | Load `.env.<name>` before running. |

### Deploy Or Update Schedule

```bash
uv run agent-scheduler deploy examples/stock_market_close_summary_daily.json
```

Purpose: create or update a Prefect deployment from payload.

Equivalent:

```bash
uv run agent-scheduler schedule create examples/stock_market_close_summary_daily.json
uv run agent-scheduler schedule update examples/stock_market_close_summary_daily.json
```

Deploy is an upsert by deployment name.

### Trigger Existing Deployment

```bash
uv run agent-scheduler run-now \
  --deployment agent-scheduler-run-workflow/daily-stock-market-close-summary
```

Purpose: create a flow run from an existing Prefect deployment.

This requires:

- Prefect server running
- deployment already created
- a worker polling the matching work pool

### List Schedules

```bash
uv run agent-scheduler schedule list
uv run agent-scheduler schedule list --limit 50 --offset 0
```

Purpose: list known Prefect deployments.

### Inspect Schedule

```bash
uv run agent-scheduler schedule inspect \
  agent-scheduler-run-workflow/daily-stock-market-close-summary
```

Purpose: inspect one deployment by UUID or `flow/deployment` name.

### Pause Schedule

```bash
uv run agent-scheduler schedule pause \
  agent-scheduler-run-workflow/daily-stock-market-close-summary
```

Purpose: pause future scheduled runs.

### Resume Schedule

```bash
uv run agent-scheduler schedule resume \
  agent-scheduler-run-workflow/daily-stock-market-close-summary
```

Purpose: resume future scheduled runs.

### Delete Schedule

```bash
uv run agent-scheduler schedule delete \
  agent-scheduler-run-workflow/daily-stock-market-close-summary
```

Purpose: delete the Prefect deployment.

## Make Targets

Use Make targets for local operation.

| Target | Purpose |
|---|---|
| `make setup` | Create `.venv` and install dependencies with `uv`. |
| `make test` | Run pytest. |
| `make help` | Show CLI help. |
| `make cli-help` | Alias for `make help`. |
| `make services-up` | Start local Postgres and Prefect server. |
| `make services-down` | Stop local services and worker profile containers. |
| `make services-logs` | Tail Postgres and Prefect server logs. |
| `make services-ps` | Show Docker Compose service status. |
| `make db-bootstrap-existing` | Apply database bootstrap to an existing local Postgres volume. |
| `make db-check-access` | Smoke-check scheduler, public pipeline, and private trading database access. |
| `make compose-config` | Render Docker Compose config. |
| `make worker` | Start generic host process worker. |
| `make worker-background` | Start generic host process worker in the background and write logs to `.logs/`. |
| `make worker-stop` | Stop the generic host worker started by `make worker-background`. |
| `make worker-opencode` | Start host process worker named for OpenCode. |
| `make worker-opencode-background` | Start host OpenCode worker in the background and write logs to `.logs/`. |
| `make worker-opencode-stop` | Stop the OpenCode worker started by `make worker-opencode-background`. |
| `make worker-claude` | Start host process worker named for Claude. |
| `make worker-claude-background` | Start host Claude worker in the background and write logs to `.logs/`. |
| `make worker-claude-stop` | Stop the Claude worker started by `make worker-claude-background`. |
| `make worker-docker` | Start container worker. Requires selected runner CLI in image. |
| `make worker-opencode-docker` | Start container OpenCode worker. Requires OpenCode in image. |
| `make smoke-run-fake` | Validate smoke payload with fake runner. |
| `make smoke-deploy` | Deploy smoke workflow. |
| `make smoke-run-deployment` | Trigger smoke deployment. |
| `make test-stock-market-close-summary` | Validate stock market close summary payload with fake runner. |
| `make flow-stock-market-close-summary-deploy` | Deploy stock market close summary schedule. |
| `make flow-stock-market-close-summary-schedule` | Alias for deploy. |
| `make flow-stock-market-close-summary-run` | Trigger stock market close summary deployment now. |

Make variables:

| Variable | Default |
|---|---|
| `ENV_FILE` | `.env.local` |
| `PREFECT_API_URL` | `http://127.0.0.1:4200/api` |
| `PREFECT_WORK_POOL` | `agent-scheduler` |
| `PREFECT_WORKER_NAME` | `agent-scheduler-worker` |
| `OPENCODE_WORKER_NAME` | `agent-scheduler-opencode-worker` |
| `CLAUDE_WORKER_NAME` | `agent-scheduler-claude-worker` |
| `WORKER_LIMIT` | `2` |
| `PAYLOAD` | `examples/stock_market_close_summary_daily.json` |
| `SMOKE_PAYLOAD` | `examples/opencode_smoke.json` |
| `POSTGRES_BOOTSTRAP_USER` | `prefect` |
| `POSTGRES_BOOTSTRAP_DB` | `prefect` |

Override example:

```bash
PAYLOAD=examples/custom_payload.json make flow-stock-market-close-summary-deploy
WORKER_LIMIT=4 make worker-opencode
```

## Local End-To-End Procedure

1. Install prerequisites.

2. Create env file:

```bash
cp .env.example .env.local
```

3. Install Python dependencies:

```bash
make setup
```

4. Validate payload:

```bash
make test-stock-market-close-summary
```

5. Start services:

```bash
make services-up
make services-ps
```

On a fresh Postgres volume, verify database and schema access:

```bash
make db-check-access
```

For a local Postgres volume created before the separated database layout:

```bash
make db-bootstrap-existing
make db-check-access
```

6. Start worker in another terminal:

```bash
make worker-opencode
```

For Claude:

```bash
make worker-claude
```

7. Deploy:

```bash
make flow-stock-market-close-summary-deploy
```

8. Trigger:

```bash
make flow-stock-market-close-summary-run
```

9. Inspect:

```bash
find outputs -maxdepth 4 -type f -print
cat outputs/daily-stock-market-close-summary.done.json
cat outputs/market-close-summary/2026-05-26/summary.md
```

10. Open Prefect UI:

```text
http://127.0.0.1:4200
```

## Runner-Specific Payload Examples

OpenCode:

```json
{
  "runner": "opencode"
}
```

Claude:

```json
{
  "runner": "claude"
}
```

Codex:

```json
{
  "runner": "codex"
}
```

## Backfill Pattern

Prefer `backfill run` for ad-hoc historical execution from an existing payload:

```bash
uv run agent-scheduler backfill run examples/stock_market_close_summary_daily.json \
  --var market_close_date=2026-05-26 \
  --asset GEMI \
  --asset PLTR \
  --set completion_signal_path=outputs/stock-market-close-summary-2026-05-26.done.json
```

For many dates, invoke `backfill run` once per date from the calling harness.

Use a one-shot payload only when the historical run itself should be stored as a Prefect deployment:

```bash
uv run agent-scheduler deploy path/to/backfill_payload.json
```

## Notes For AI Harnesses

- Prefer `run_prompt` for new work.
- Use `--fake` before deploy to verify prompt rendering.
- Keep prompt artifacts and scheduler completion signals separate.
- Do not write generated artifacts into git-tracked paths unless explicitly required.
- Do not edit Prefect Postgres tables directly; use CLI/API/UI.
- If changing future scheduled defaults, update deployment parameters and redeploy.
- If running historical work, submit one-shot schedules or direct runs with date-specific payloads.
- Always specify timezone.
- Prefer stable deployment names.
