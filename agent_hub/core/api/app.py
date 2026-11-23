"""Compose API routers and translate typed failures consistently."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from agent_hub.core.api import health, routes_agents, routes_chat, routes_conversations
from agent_hub.core.errors import ErrorCode, HubError


def configure_routes(app: FastAPI) -> None:
    @app.exception_handler(HubError)
    async def hub_error(request: Request, error: HubError) -> JSONResponse:
        status = 404 if error.code == ErrorCode.NOT_FOUND else 400
        return JSONResponse(
            status_code=status, content={"code": error.code, "message": error.message}
        )

    for router in (
        health.router,
        routes_agents.router,
        routes_conversations.router,
        routes_chat.router,
    ):
        app.include_router(router)
