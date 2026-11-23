"""Agent catalog and safe avatar serving."""

from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import FileResponse

from agent_hub.core.errors import ErrorCode, HubError
from agent_hub.core.registry.registry import CompiledAgent

router = APIRouter(prefix="/api/agents")


def describe(agent: CompiledAgent) -> dict[str, Any]:
    definition = agent.definition
    return {
        "name": definition.name,
        "display_name": definition.display_name,
        "description": definition.description,
        "avatar": definition.avatar if not agent.avatar_file else "💬",
        "avatar_url": f"/api/agents/{definition.name}/avatar" if agent.avatar_file else None,
        "accent_color": definition.accent_color,
        "tags": definition.tags,
        "starter_prompts": definition.starter_prompts,
        "tools": [
            {"native": tool.native, "user_toggle": tool.user_toggle} for tool in definition.tools
        ],
    }


@router.get("")
async def agents(request: Request) -> list[dict[str, Any]]:
    return [describe(agent) for agent in request.app.state.registry.all()]


@router.get("/{name}")
async def detail(name: str, request: Request) -> dict[str, Any]:
    return describe(request.app.state.registry.get(name))


@router.get("/{name}/avatar")
async def avatar(name: str, request: Request) -> FileResponse:
    path = request.app.state.registry.get(name).avatar_file
    if not path:
        raise HubError(ErrorCode.NOT_FOUND, "This agent has no avatar file")
    return FileResponse(
        path,
        headers={
            "Content-Security-Policy": "default-src 'none'; sandbox",
            "X-Content-Type-Options": "nosniff",
        },
    )
