"""Offline test helpers shared across unit and API suites."""

import asyncio
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

from pydantic_ai.messages import ModelMessage
from pydantic_ai.models.function import AgentInfo, FunctionModel

from agent_hub.core.registry.definition import AgentDefinition
from agent_hub.core.registry.registry import CompiledAgent


def fixture_agent(**overrides: Any) -> CompiledAgent:
    data: dict[str, Any] = {
        "name": "fixture-bot",
        "display_name": "Fixture Bot",
        "description": "Fictional test agent",
        "harness": {
            "system_prompt": "Test instructions",
            "loop": {"type": "basic", "max_iterations": 6, "timeout_seconds": 5},
        },
    }
    data.update(overrides)
    return CompiledAgent(AgentDefinition.model_validate(data), "Test instructions", Path("."))


def scripted_model(
    chunks: list[str], delay: float = 0, error: Exception | None = None
) -> FunctionModel:
    async def stream(messages: list[ModelMessage], info: AgentInfo) -> AsyncIterator[str]:
        for chunk in chunks:
            if delay:
                await asyncio.sleep(delay)
            yield chunk
        if error:
            raise error

    return FunctionModel(stream_function=stream, model_name="scripted")


class FakeClock:
    def __init__(self) -> None:
        self.sleeps: list[float] = []

    async def sleep(self, seconds: float) -> None:
        self.sleeps.append(seconds)
