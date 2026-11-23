"""Smoke checks for the installed CLI shell."""

from typer.testing import CliRunner

from agent_hub.cli import app


def test_cli_help() -> None:
    result = CliRunner().invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "validate" in result.output
