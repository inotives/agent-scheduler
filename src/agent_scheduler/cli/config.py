from __future__ import annotations

import json
from typing import Annotated

import typer
from pydantic import ValidationError

from agent_scheduler.config.settings import load_settings


app = typer.Typer(help="Inspect scheduler configuration.")


@app.command("check")
def check_config(
    env: Annotated[
        str | None,
        typer.Option("--env", help="Environment name matching .env.<name>."),
    ] = None,
) -> None:
    """Validate the selected environment configuration."""
    try:
        settings = load_settings(env=env)
    except ValidationError as exc:
        typer.echo(
            json.dumps(
                {
                    "ok": False,
                    "error": {
                        "code": "invalid_config",
                        "message": "Configuration validation failed.",
                        "details": exc.errors(include_url=False),
                    },
                }
            )
        )
        raise typer.Exit(code=1) from exc

    typer.echo(
        json.dumps(
            {
                "ok": True,
                "env": settings.app_env,
                "prefect_api_url": settings.prefect_api_url,
                "prefect_database_configured": True,
                "agent_scheduler_database_configured": True,
                "pipeline_database_configured": True,
                "trading_private_database_configured": True,
                "coingecko_api_base_url": settings.coingecko_api_base_url,
                "coingecko_api_key_configured": bool(settings.coingecko_api_key),
            }
        )
    )
