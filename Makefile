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
POSTGRES_PORT ?= 5432
PIPELINE_DB_NAME ?= pipeline_data
PIPELINE_DB_USER ?= pipeline_app
PIPELINE_DB_PASSWORD ?= pipeline_app
LOCAL_PIPELINE_DATABASE_URL ?= postgresql+asyncpg://$(PIPELINE_DB_USER):$(PIPELINE_DB_PASSWORD)@127.0.0.1:$(POSTGRES_PORT)/$(PIPELINE_DB_NAME)

export UV_CACHE_DIR ?= .uv-cache
export PREFECT_HOME

.PHONY: setup test help cli-help services-up services-down services-logs services-ps db-bootstrap-existing db-check-access worker worker-background worker-stop worker-opencode worker-opencode-background worker-opencode-stop worker-claude worker-claude-background worker-claude-stop worker-docker worker-opencode-docker compose-config pipeline-coingecko-coins-dry-run pipeline-coingecko-coins-ingest pipeline-coingecko-asset-platforms-dry-run pipeline-coingecko-asset-platforms-ingest pipeline-coingecko-nfts-dry-run pipeline-coingecko-nfts-ingest pipeline-coingecko-deploy-schedules pipeline-coingecko-coins-run-deployment pipeline-coingecko-asset-platforms-run-deployment pipeline-coingecko-nfts-run-deployment smoke-run-fake smoke-deploy smoke-run-deployment test-stock-market-close-summary flow-stock-market-close-summary-deploy flow-stock-market-close-summary-schedule flow-stock-market-close-summary-run

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

worker-background:
	@mkdir -p .logs
	@sh -c 'PREFECT_API_URL=$(PREFECT_API_URL) $(UV) run prefect worker start --pool $(PREFECT_WORK_POOL) --type process --limit $(WORKER_LIMIT) --name $(PREFECT_WORKER_NAME) --install-policy never > .logs/$(PREFECT_WORKER_NAME).log 2>&1 & pid=$$!; printf "%s\n" "$$pid" > .logs/$(PREFECT_WORKER_NAME).pid; printf "%s\n" "$$pid"'

worker-stop:
	@sh -c 'test -f .logs/$(PREFECT_WORKER_NAME).pid || { echo "No PID file for $(PREFECT_WORKER_NAME)"; exit 1; }; pid=$$(cat .logs/$(PREFECT_WORKER_NAME).pid); kill "$$pid"; rm -f .logs/$(PREFECT_WORKER_NAME).pid; echo "Stopped $(PREFECT_WORKER_NAME) ($$pid)"'

worker-opencode:
	PREFECT_API_URL=$(PREFECT_API_URL) $(UV) run prefect worker start --pool $(PREFECT_WORK_POOL) --type process --limit $(WORKER_LIMIT) --name $(OPENCODE_WORKER_NAME) --install-policy never

worker-opencode-background:
	@mkdir -p .logs
	@sh -c 'PREFECT_API_URL=$(PREFECT_API_URL) $(UV) run prefect worker start --pool $(PREFECT_WORK_POOL) --type process --limit $(WORKER_LIMIT) --name $(OPENCODE_WORKER_NAME) --install-policy never > .logs/$(OPENCODE_WORKER_NAME).log 2>&1 & pid=$$!; printf "%s\n" "$$pid" > .logs/$(OPENCODE_WORKER_NAME).pid; printf "%s\n" "$$pid"'

worker-opencode-stop:
	@sh -c 'test -f .logs/$(OPENCODE_WORKER_NAME).pid || { echo "No PID file for $(OPENCODE_WORKER_NAME)"; exit 1; }; pid=$$(cat .logs/$(OPENCODE_WORKER_NAME).pid); kill "$$pid"; rm -f .logs/$(OPENCODE_WORKER_NAME).pid; echo "Stopped $(OPENCODE_WORKER_NAME) ($$pid)"'

worker-claude:
	PREFECT_API_URL=$(PREFECT_API_URL) $(UV) run prefect worker start --pool $(PREFECT_WORK_POOL) --type process --limit $(WORKER_LIMIT) --name $(CLAUDE_WORKER_NAME) --install-policy never

worker-claude-background:
	@mkdir -p .logs
	@sh -c 'PREFECT_API_URL=$(PREFECT_API_URL) $(UV) run prefect worker start --pool $(PREFECT_WORK_POOL) --type process --limit $(WORKER_LIMIT) --name $(CLAUDE_WORKER_NAME) --install-policy never > .logs/$(CLAUDE_WORKER_NAME).log 2>&1 & pid=$$!; printf "%s\n" "$$pid" > .logs/$(CLAUDE_WORKER_NAME).pid; printf "%s\n" "$$pid"'

worker-claude-stop:
	@sh -c 'test -f .logs/$(CLAUDE_WORKER_NAME).pid || { echo "No PID file for $(CLAUDE_WORKER_NAME)"; exit 1; }; pid=$$(cat .logs/$(CLAUDE_WORKER_NAME).pid); kill "$$pid"; rm -f .logs/$(CLAUDE_WORKER_NAME).pid; echo "Stopped $(CLAUDE_WORKER_NAME) ($$pid)"'

worker-docker:
	$(COMPOSE) --env-file $(ENV_FILE) --profile worker up prefect-worker

worker-opencode-docker:
	$(COMPOSE) --env-file $(ENV_FILE) --profile worker up prefect-worker-opencode

compose-config:
	$(COMPOSE) --env-file $(ENV_FILE) config

pipeline-coingecko-coins-dry-run:
	$(UV) run python pipelines/coingecko/ingest_coins.py --dry-run

pipeline-coingecko-coins-ingest:
	PIPELINE_DATABASE_URL=$(LOCAL_PIPELINE_DATABASE_URL) $(UV) run python pipelines/coingecko/ingest_coins.py --include-platform

pipeline-coingecko-asset-platforms-dry-run:
	$(UV) run python pipelines/coingecko/ingest_asset_platforms.py --dry-run

pipeline-coingecko-asset-platforms-ingest:
	PIPELINE_DATABASE_URL=$(LOCAL_PIPELINE_DATABASE_URL) $(UV) run python pipelines/coingecko/ingest_asset_platforms.py

pipeline-coingecko-nfts-dry-run:
	$(UV) run python pipelines/coingecko/ingest_nfts.py --dry-run --max-pages 1

pipeline-coingecko-nfts-ingest:
	PIPELINE_DATABASE_URL=$(LOCAL_PIPELINE_DATABASE_URL) $(UV) run python pipelines/coingecko/ingest_nfts.py

pipeline-coingecko-deploy-schedules:
	PIPELINE_DATABASE_URL=$(LOCAL_PIPELINE_DATABASE_URL) PREFECT_API_URL=$(PREFECT_API_URL) $(UV) run python pipelines/coingecko/deploy_schedules.py

pipeline-coingecko-coins-run-deployment:
	PREFECT_API_URL=$(PREFECT_API_URL) $(UV) run prefect deployment run coingecko-ingest-coins/weekly-coingecko-coins-list

pipeline-coingecko-asset-platforms-run-deployment:
	PREFECT_API_URL=$(PREFECT_API_URL) $(UV) run prefect deployment run coingecko-ingest-asset-platforms/weekly-coingecko-asset-platforms

pipeline-coingecko-nfts-run-deployment:
	PREFECT_API_URL=$(PREFECT_API_URL) $(UV) run prefect deployment run coingecko-ingest-nfts-list/weekly-coingecko-nfts-list

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
