"""Health reflects actual model, search, and tracing configuration."""

from typing import Any

from fastapi import APIRouter, Request

router = APIRouter()


@router.get("/health")
async def health(request: Request) -> dict[str, Any]:
    settings = request.app.state.settings
    agents = request.app.state.registry.all()
    online = any(
        not settings.is_demo(agent.definition.harness.model.deployment) for agent in agents
    )
    if not agents:
        online = not settings.is_demo()
    return {
        "status": "ok",
        "model_mode": "foundry" if online else "demo",
        "search_provider": settings.search_provider if online else "fake",
        "tracing": "on" if any(t.enabled for t in request.app.state.tracers.values()) else "off",
        "max_message_chars": settings.max_message_chars,
    }
