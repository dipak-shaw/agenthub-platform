"""A streaming engine boundary independent of transport and persistence."""

from collections.abc import AsyncIterator
from typing import Protocol

from pydantic_ai.messages import ModelMessage

from agent_hub.core.chat.events import StreamEvent


class LoopEngine(Protocol):
    def stream(
        self,
        run_id: str,
        message: str,
        history: list[ModelMessage],
        web_search_enabled: bool = True,
    ) -> AsyncIterator[StreamEvent]: ...
