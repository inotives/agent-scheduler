UV ?= uv
COMPOSE ?= docker compose
ENV_FILE ?= .env.local
PREFECT_API_URL ?= http://127.0.0.1:4200/api
PREFECT_HOME ?= .prefect
PREFECT_WORK_POOL ?= agent-scheduler
PREFECT_WORKER_NAME ?= agent-scheduler-worker
OPENCODE_WORKER_NAME ?= agent-scheduler-opencode-worker
CLAUDE_WORKER_NAME ?= agent-scheduler-claude-worker
WORKER_LIMIT ?= 2
PAYLOAD ?= examples/stock_market_close_summary_daily.json
SMOKE_PAYLOAD ?= examples/opencode_smoke.json
POSTGRES_BOOTSTRAP_USER ?= prefect
POSTGRES_BOOTSTRAP_DB ?= prefect

export UV_CACHE_DIR ?= .uv-cache
export PREFECT_HOME

.PHONY: setup test help cli-help services-up services-down services-logs services-ps db-bootstrap-existing db-check-access worker worker-opencode worker-claude worker-docker worker-opencode-docker compose-config smoke-run-fake smoke-deploy smoke-run-deployment test-stock-market-close-summary flow-stock-market-close-summary-deploy flow-stock-market-close-summary-schedule flow-stock-market-close-summary-run

setup:
	$(UV) venv --allow-existing
	$(UV) sync

test:
	$(UV) run pytest

help:
	$(UV) run agent-scheduler --help

cli-help: help

services-up:
	$(COMPOSE) --env-file $(ENV_FILE) up -d postgres prefect-server

services-down:
	$(COMPOSE) --env-file $(ENV_FILE) --profile worker down

services-logs:
	$(COMPOSE) --env-file $(ENV_FILE) logs -f postgres prefect-server

services-ps:
	$(COMPOSE) --env-file $(ENV_FILE) ps

db-bootstrap-existing:
	$(COMPOSE) --env-file $(ENV_FILE) exec -T -e POSTGRES_USER=$(POSTGRES_BOOTSTRAP_USER) -e POSTGRES_DB=$(POSTGRES_BOOTSTRAP_DB) postgres /docker-entrypoint-initdb.d/010-create-databases.sh

db-check-access:
	$(COMPOSE) --env-file $(ENV_FILE) exec -T postgres sh -c 'PGPASSWORD="$${AGENT_SCHEDULER_DB_PASSWORD:-agent_scheduler}" psql -h 127.0.0.1 -U "$${AGENT_SCHEDULER_DB_USER:-agent_scheduler_app}" -d "$${AGENT_SCHEDULER_DB_NAME:-agent_scheduler}" -v ON_ERROR_STOP=1 -c "CREATE TABLE IF NOT EXISTS scheduler_app.access_smoke (checked_at timestamptz DEFAULT now()); DROP TABLE scheduler_app.access_smoke;"'
	$(COMPOSE) --env-file $(ENV_FILE) exec -T postgres sh -c 'PGPASSWORD="$${PIPELINE_DB_PASSWORD:-pipeline_app}" psql -h 127.0.0.1 -U "$${PIPELINE_DB_USER:-pipeline_app}" -d "$${PIPELINE_DB_NAME:-pipeline_data}" -v ON_ERROR_STOP=1 -c "CREATE TABLE IF NOT EXISTS public_data.access_smoke (checked_at timestamptz DEFAULT now()); DROP TABLE public_data.access_smoke;"'
	$(COMPOSE) --env-file $(ENV_FILE) exec -T postgres sh -c 'PGPASSWORD="$${TRADING_PRIVATE_DB_PASSWORD:-trading_private}" psql -h 127.0.0.1 -U "$${TRADING_PRIVATE_DB_USER:-trading_private_writer}" -d "$${PIPELINE_DB_NAME:-pipeline_data}" -v ON_ERROR_STOP=1 -c "CREATE TABLE IF NOT EXISTS trading_private.access_smoke (checked_at timestamptz DEFAULT now()); DROP TABLE trading_private.access_smoke;"'

worker:
	PREFECT_API_URL=$(PREFECT_API_URL) $(UV) run prefect worker start --pool $(PREFECT_WORK_POOL) --type process --limit $(WORKER_LIMIT) --name $(PREFECT_WORKER_NAME) --install-policy never

worker-opencode:
	PREFECT_API_URL=$(PREFECT_API_URL) $(UV) run prefect worker start --pool $(PREFECT_WORK_POOL) --type process --limit $(WORKER_LIMIT) --name $(OPENCODE_WORKER_NAME) --install-policy never

worker-claude:
	PREFECT_API_URL=$(PREFECT_API_URL) $(UV) run prefect worker start --pool $(PREFECT_WORK_POOL) --type process --limit $(WORKER_LIMIT) --name $(CLAUDE_WORKER_NAME) --install-policy never

worker-docker:
	$(COMPOSE) --env-file $(ENV_FILE) --profile worker up prefect-worker

worker-opencode-docker:
	$(COMPOSE) --env-file $(ENV_FILE) --profile worker up prefect-worker-opencode

compose-config:
	$(COMPOSE) --env-file $(ENV_FILE) config

smoke-run-fake:
	$(UV) run agent-scheduler run-now --payload $(SMOKE_PAYLOAD) --fake

smoke-deploy:
	$(UV) run agent-scheduler deploy $(SMOKE_PAYLOAD)

smoke-run-deployment:
	$(UV) run agent-scheduler run-now --deployment agent-scheduler-run-workflow/opencode-smoke

test-stock-market-close-summary:
	$(UV) run agent-scheduler run-now --payload $(PAYLOAD) --fake

flow-stock-market-close-summary-deploy:
	$(UV) run agent-scheduler deploy $(PAYLOAD)

flow-stock-market-close-summary-schedule: flow-stock-market-close-summary-deploy

flow-stock-market-close-summary-run:
	$(UV) run agent-scheduler run-now --deployment agent-scheduler-run-workflow/daily-stock-market-close-summary
