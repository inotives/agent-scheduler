UV ?= uv
COMPOSE ?= docker compose
ENV_FILE ?= .env.local
PREFECT_API_URL ?= http://127.0.0.1:4200/api
PREFECT_HOME ?= .prefect
PREFECT_WORK_POOL ?= agent-scheduler
PREFECT_WORKER_NAME ?= agent-scheduler-worker
WORKER_LIMIT ?= 2

export UV_CACHE_DIR ?= .uv-cache
export PREFECT_HOME

.PHONY: setup test help cli-help services-up services-down services-logs services-ps worker worker-docker compose-config

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

worker-docker:
	$(COMPOSE) --env-file $(ENV_FILE) --profile worker up prefect-worker

compose-config:
	$(COMPOSE) --env-file $(ENV_FILE) config
