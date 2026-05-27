from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import typer
from pydantic import ValidationError


def echo_json(payload: dict[str, Any], exit_code: int = 0) -> None:
    typer.echo(json.dumps(payload, default=str))
    if exit_code:
        raise typer.Exit(code=exit_code)


def echo_error(code: str, message: str, details: Any = None, exit_code: int = 1) -> None:
    error: dict[str, Any] = {"code": code, "message": message}
    if details is not None:
        error["details"] = details
    echo_json({"ok": False, "error": error}, exit_code=exit_code)


def validation_details(exc: ValidationError) -> list[dict[str, Any]]:
    return exc.errors(include_url=False)


def read_json_file(path: Path) -> dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except OSError as exc:
        raise ValueError(f"Could not read payload file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON payload file: {path}") from exc

    if not isinstance(payload, dict):
        raise ValueError("Payload must be a JSON object")
    return payload
