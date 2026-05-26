UV ?= uv
export UV_CACHE_DIR ?= .uv-cache

.PHONY: setup test help cli-help

setup:
	$(UV) venv --allow-existing
	$(UV) sync

test:
	$(UV) run pytest

help:
	$(UV) run agent-scheduler --help

cli-help: help
