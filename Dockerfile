FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

ENV PATH="/app/.venv/bin:${PATH}" \
    PREFECT_HOME="/app/.prefect" \
    PYTHONUNBUFFERED="1" \
    UV_CACHE_DIR="/tmp/uv-cache" \
    UV_COMPILE_BYTECODE="1" \
    UV_LINK_MODE="copy"

WORKDIR /app

COPY pyproject.toml uv.lock README.md ./
COPY src ./src

RUN uv sync --frozen --no-dev

CMD ["agent-scheduler", "--help"]

