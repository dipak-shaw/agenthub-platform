"""Resolve environment references without logging their values."""

import os

from agent_hub.core.errors import ConfigError


def resolve(value: str, file: str, field: str) -> str:
    """Resolve a literal or a required environment reference."""
    if not value.startswith("os.environ/"):
        return value
    name = value.removeprefix("os.environ/")
    result = os.environ.get(name, "")
    if not result.strip():
        raise ConfigError(file, field, f"environment variable {name!r} is missing or empty")
    return result
