"""POST streaming over SSE; closing the stream cancels and saves partial output."""

from collections.abc import AsyncIterator

from fastapi import APIRouter, Request, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, ConfigDict, Field

from agent_hub.core.errors import ErrorCode, HubError

router = APIRouter(prefix="/api")


class ChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    conversation_id: str | None = None
    message: str = Field(min_length=1, max_length=100000)
    web_search_enabled: bool = True
    regenerate: bool = False


@router.post("/agents/{name}/chat")
async def chat(name: str, body: ChatRequest, request: Request) -> StreamingResponse:
    if len(body.message) > request.app.state.settings.max_message_chars:
        raise HubError(ErrorCode.CONFIG_INVALID, "Message exceeds the character limit")
    service = request.app.state.chat
    run = await service.start(
        name, body.message, body.conversation_id, body.web_search_enabled, body.regenerate
    )

    async def generate() -> AsyncIterator[str]:
        async for event in service.events(run):
            yield f"data: {event.model_dump_json()}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "X-Run-ID": run.id,
        },
    )


@router.post("/runs/{run_id}/stop", status_code=204)
async def stop(run_id: str, request: Request) -> Response:
    await request.app.state.chat.stop(run_id)
    return Response(status_code=204)
