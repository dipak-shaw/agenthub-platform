"""Deterministic discovery without importing per-agent code."""

from pathlib import Path

from agent_hub.core.errors import ConfigError


def discover(root: Path) -> list[Path]:
    if not root.is_dir():
        raise ConfigError(str(root), "agents_dir", "directory does not exist")
    return sorted(root.glob("*/agent.yaml"))
