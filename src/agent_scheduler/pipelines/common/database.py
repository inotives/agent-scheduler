from __future__ import annotations

from urllib.parse import urlsplit, urlunsplit


def to_asyncpg_dsn(database_url: str) -> str:
    """Normalize SQLAlchemy-style Postgres URLs for asyncpg."""
    if database_url.startswith("postgresql+asyncpg://"):
        return "postgresql://" + database_url.removeprefix("postgresql+asyncpg://")
    return database_url


def redact_database_url(database_url: str) -> str:
    parsed = urlsplit(database_url)
    if not parsed.password:
        return database_url

    username = parsed.username or ""
    hostname = parsed.hostname or ""
    port = f":{parsed.port}" if parsed.port else ""
    userinfo = f"{username}:***@" if username else ""
    netloc = f"{userinfo}{hostname}{port}"
    return urlunsplit((parsed.scheme, netloc, parsed.path, parsed.query, parsed.fragment))
