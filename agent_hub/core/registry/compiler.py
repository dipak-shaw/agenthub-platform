"""Compile every discovered agent before publishing a registry."""

from pathlib import Path

from agent_hub.core.errors import ConfigError
from agent_hub.core.registry.discovery import discover
from agent_hub.core.registry.loader import load
from agent_hub.core.registry.registry import AgentRegistry

REGISTERED_ENGINES = frozenset({"basic"})


def compile_registry(root: Path) -> AgentRegistry:
    registry = AgentRegistry()
    errors: list[str] = []
    for path in discover(root):
        try:
            agent = load(path)
            if agent.definition.harness.loop.type not in REGISTERED_ENGINES:
                raise ConfigError(str(path), "harness.loop.type", "unknown loop engine")
            names = [tool.native for tool in agent.definition.tools]
            if len(set(names)) != len(names):
                raise ConfigError(str(path), "tools", "duplicate native tool")
            registry.add(agent)
        except ConfigError as exc:
            errors.append(exc.message)
    if errors:
        raise ConfigError(str(root), "$", "\n".join(errors))
    return registry
