# Prefect Runtime

The local runtime uses a self-hosted Prefect server backed by Postgres.

## Local Services

```bash
make services-up
make services-ps
make services-logs
```

`make services-up` starts:

- `postgres`
- `prefect-server`

The Prefect API is exposed at `http://127.0.0.1:4200/api`.

## Workers

Run a local process worker against the local Prefect API:

```bash
make worker
```

Run the worker in Docker:

```bash
make worker-docker
```

## Configuration

Local defaults live in `.env.local`, which is gitignored. Safe defaults are documented in `.env.example`.

The required database setting is:

```bash
PREFECT_API_DATABASE_CONNECTION_URL=postgresql+asyncpg://prefect:prefect@postgres:5432/prefect
```

SQLite is not a project default.
