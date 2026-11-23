"""Validated runtime agents indexed by their stable URL name."""

from dataclasses import dataclass
from pathlib import Path

from agent_hub.core.errors import ConfigError, ErrorCode, HubError
from agent_hub.core.registry.definition import AgentDefinition


@dataclass(frozen=True)
class CompiledAgent:
    definition: AgentDefinition
    system_prompt: str
    folder: Path
    avatar_file: Path | None = None


class AgentRegistry:
    def __init__(self) -> None:
        self._agents: dict[str, CompiledAgent] = {}

    def add(self, agent: CompiledAgent) -> None:
        name = agent.definition.name
        if name in self._agents:
            raise ConfigError(str(agent.folder / "agent.yaml"), "name", f"duplicate name {name!r}")
        self._agents[name] = agent

    def get(self, name: str) -> CompiledAgent:
        try:
            return self._agents[name]
        except KeyError as exc:
            raise HubError(ErrorCode.NOT_FOUND, f"Agent {name!r} was not found") from exc

    def all(self) -> list[CompiledAgent]:
        return list(self._agents.values())
