"""Conversation CRUD; a running turn must be stopped before deleting its chat."""

from fastapi import APIRouter, Request, Response
from pydantic import BaseModel, ConfigDict, Field

from agent_hub.core.errors import ErrorCode, HubError
from agent_hub.core.storage.tables import ConversationDetail, ConversationRecord

router = APIRouter(prefix="/api/conversations")


class Rename(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    title: str = Field(min_length=1, max_length=60)


@router.get("")
async def conversations(request: Request, agent: str | None = None) -> list[ConversationRecord]:
    return await request.app.state.repository.list(agent)  # type: ignore[no-any-return]


@router.get("/{conversation_id}")
async def conversation(conversation_id: str, request: Request) -> ConversationDetail:
    return await request.app.state.repository.get(conversation_id)  # type: ignore[no-any-return]


@router.patch("/{conversation_id}")
async def rename(conversation_id: str, body: Rename, request: Request) -> ConversationRecord:
    return await request.app.state.repository.rename(conversation_id, body.title)  # type: ignore[no-any-return]


@router.delete("/{conversation_id}", status_code=204)
async def delete(conversation_id: str, request: Request) -> Response:
    service = request.app.state.chat
    async with service.lock:
        if any(run.conversation_id == conversation_id for run in service.runs.values()):
            raise HubError(
                ErrorCode.CONFIG_INVALID, "Stop the active response before deleting this chat"
            )
        await request.app.state.repository.delete(conversation_id)
    return Response(status_code=204)
