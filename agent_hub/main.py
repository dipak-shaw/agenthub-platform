"""App factory: validate all agents before opening the database and serving traffic."""

from collections.abc import AsyncIterator
from contextlib import AsyncExitStack, asynccontextmanager

from fastapi import FastAPI

from agent_hub.core.api.app import configure_routes
from agent_hub.core.api.static import mount_web
from agent_hub.core.chat.service import ChatService
from agent_hub.core.loop_engines.basic import BasicEngine
from agent_hub.core.models.provider import build_model, close_model
from agent_hub.core.observability.factory import build_tracer
from agent_hub.core.registry.compiler import compile_registry
from agent_hub.core.registry.registry import CompiledAgent
from agent_hub.core.settings import Settings
from agent_hub.core.storage.db import create_database, initialize
from agent_hub.core.storage.repository import SQLiteRepository


def create_app(settings: Settings | None = None) -> FastAPI:
    config = settings or Settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        registry = compile_registry(config.agents_dir)
        database = create_database(config.database_url)
        await initialize(database)
        repository = SQLiteRepository(database)
        global_tracer = build_tracer(config)
        tracers = {
            agent.definition.name: (
                build_tracer(config, agent.definition.runtime.tracing)
                if agent.definition.runtime.tracing
                else global_tracer
            )
            for agent in registry.all()
        }
        tracers[""] = global_tracer

        models = {}
        resources = AsyncExitStack()
        try:
            for agent in registry.all():
                model = build_model(config, agent.definition.harness.model.deployment)
                models[agent.definition.name] = model
                resources.push_async_callback(close_model, model)
        except BaseException:
            await resources.aclose()
            await database.dispose()
            raise

        def engine(agent: CompiledAgent) -> BasicEngine:
            return BasicEngine(
                agent, config, models[agent.definition.name], tracers[agent.definition.name]
            )

        service = ChatService(registry, repository, engine, lambda name: tracers[name])
        app.state.settings, app.state.registry = config, registry
        app.state.repository, app.state.chat, app.state.tracers = repository, service, tracers
        try:
            yield
        finally:
            await service.close()
            await resources.aclose()
            await database.dispose()

    app = FastAPI(title="Agent Hub", version="0.1.0", lifespan=lifespan)
    configure_routes(app)
    mount_web(app, config.web_dist)
    return app
