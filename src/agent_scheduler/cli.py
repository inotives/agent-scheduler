from __future__ import annotations

import json
from typing import Annotated

import typer

from agent_scheduler import __version__


app = typer.Typer(
    name="agent-scheduler",
    help="Schedule headless agent workflows through Prefect.",
    no_args_is_help=True,
)


@app.callback()
def main(
    version: Annotated[
        bool,
        typer.Option("--version", help="Print the installed version and exit."),
    ] = False,
) -> None:
    if version:
        typer.echo(json.dumps({"version": __version__}))
        raise typer.Exit()


@app.command()
def health() -> None:
    """Print a machine-readable health response."""
    typer.echo(json.dumps({"status": "ok"}))

