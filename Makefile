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

export UV_CACHE_DIR ?= .uv-cache
export PREFECT_HOME

.PHONY: setup test help cli-help services-up services-down services-logs services-ps worker worker-opencode worker-claude worker-docker worker-opencode-docker compose-config smoke-run-fake smoke-deploy smoke-run-deployment test-stock-market-close-summary flow-stock-market-close-summary-deploy flow-stock-market-close-summary-schedule flow-stock-market-close-summary-run

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
