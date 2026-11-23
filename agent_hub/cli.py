"""Run, validate, or chat locally without requiring an HTTP client."""

import asyncio

import typer
import uvicorn

from agent_hub.core.chat.events import ErrorEvent, Token
from agent_hub.core.errors import HubError
from agent_hub.core.registry.compiler import compile_registry
from agent_hub.core.settings import Settings

app = typer.Typer(no_args_is_help=True, help="Config-driven Q&A agents.")


@app.command()
def run(host: str = "127.0.0.1", port: int = 8080, reload: bool = False) -> None:
    """Serve the API and built web app."""
    uvicorn.run("agent_hub.main:create_app", factory=True, host=host, port=port, reload=reload)


@app.command()
def validate() -> None:
    """Validate every configured agent and report all file/field errors."""
    try:
        registry = compile_registry(Settings().agents_dir)
    except HubError as exc:
        typer.echo(exc.message, err=True)
        raise typer.Exit(1) from exc
    typer.echo(f"Validated {len(registry.all())} agent(s).")


@app.command()
def chat(agent: str) -> None:
    """Start a persisted terminal chat; type /quit to exit."""
    from agent_hub.main import create_app

    async def session() -> None:
        application = create_app()
        async with application.router.lifespan_context(application):
            application.state.registry.get(agent)
            conversation_id = None
            while True:
                try:
                    message = await asyncio.to_thread(input, "You: ")
                except EOFError:
                    return
                if message.strip() == "/quit":
                    return
                if not message.strip():
                    continue
                run = await application.state.chat.start(
                    agent, message, conversation_id, True, False
                )
                conversation_id = run.conversation_id
                async for event in application.state.chat.events(run):
                    if isinstance(event, Token):
                        typer.echo(event.text, nl=False)
                    elif isinstance(event, ErrorEvent):
                        typer.echo(f"\n[{event.code}] {event.message}", err=True)
                typer.echo()

    try:
        asyncio.run(session())
    except HubError as exc:
        typer.echo(exc.message, err=True)
        raise typer.Exit(1) from exc
