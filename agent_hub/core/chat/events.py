"""Discriminated SSE payloads with stable run identifiers."""

from typing import Annotated, Any, Literal

from pydantic import BaseModel, Field

from agent_hub.core.errors import ErrorCode


class Source(BaseModel):
    index: int
    title: str
    url: str
    snippet: str


class Event(BaseModel):
    run_id: str


class RunStarted(Event):
    type: Literal["run_started"] = "run_started"
    conversation_id: str
    message_id: str


class ToolStart(Event):
    type: Literal["tool_start"] = "tool_start"
    tool: str
    input: dict[str, Any]


class ToolEnd(Event):
    type: Literal["tool_end"] = "tool_end"
    tool: str
    sources: list[Source]


class Token(Event):
    type: Literal["token"] = "token"
    text: str


class RunFinished(Event):
    type: Literal["run_finished"] = "run_finished"
    status: Literal["complete", "stopped", "error"]
    latency_ms: int
    tokens_in: int = 0
    tokens_out: int = 0


class ErrorEvent(Event):
    type: Literal["error"] = "error"
    code: ErrorCode
    message: str


StreamEvent = Annotated[
    RunStarted | ToolStart | ToolEnd | Token | RunFinished | ErrorEvent, Field(discriminator="type")
]
