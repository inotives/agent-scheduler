# Stock Market Close Summary

This workflow schedules the registered `run_prompt` workflow to run the stock market close summary skill for configured assets every day at 16:00 Asia/Singapore. The default example uses `GEMI` and `PLTR`; the default runner is OpenCode.

## Payload

The example payload is [examples/stock_market_close_summary_daily.json](../examples/stock_market_close_summary_daily.json).

It stores a prompt template plus variables as Prefect deployment parameters. At run time, the worker renders the final prompt and passes plain text to the selected headless agent:

```text
Run skill in examples/flows/market_close_summary for the following assets: GEMI, PLTR.

Market close date: 2026-05-26.

Generate the actual report exactly as defined by the skill instructions, including the output format and output path specified by the skill.

After the skill has produced its report, write a completion signal JSON file to outputs/daily-stock-market-close-summary.done.json with at least: {"status":"completed","assets":["GEMI","PLTR"],"market_close_date":"2026-05-26"}.
```

## Local Fake Run

Use the fake runner to verify payload validation and prompt rendering without starting Prefect or invoking OpenCode, Claude, or Codex:

```bash
make test-stock-market-close-summary
```

## Prefect Stack

Start Postgres and Prefect:

```bash
make services-up
```

Start a worker in another shell:

```bash
make worker-opencode
```

Deploy or update the daily schedule:

```bash
make flow-stock-market-close-summary-deploy
```

Trigger the deployed schedule immediately:

```bash
make flow-stock-market-close-summary-run
```

Inspect runs in the Prefect UI at `http://127.0.0.1:4200`.

## Runtime Notes

- Prefect stores state in Postgres through `PREFECT_API_DATABASE_CONNECTION_URL`.
- Prefect stores deployment parameters, including the prompt template and variables, in its Postgres backend.
- Future scheduled runs can be changed by updating deployment parameters through the Prefect UI/API/CLI; direct SQL updates are not recommended.
- Historical backfills should create ad-hoc flow runs with parameter overrides instead of editing the deployment defaults.
- The scheduler records runner status/logs in Prefect and verifies the completion signal JSON for real runners.
- The skill-generated markdown is written by the agent to the output path defined by the repo-local example skill itself, not by the scheduler payload.
- The default global agent concurrency limit is `2`.
- The workflow-specific concurrency limit is `1` per task/workspace key.
- `runner` can be `opencode`, `claude`, or `codex`; when omitted, the workflow uses `opencode`.
- The runtime that picks up real agent runs must have the selected agent CLI installed.
