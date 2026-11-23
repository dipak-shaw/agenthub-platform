"""Turn lifecycle: bounded history, cancellation, persistence, then terminal event."""

import asyncio
import logging
import time
from collections.abc import AsyncIterator, Callable
from dataclasses import dataclass, field
from uuid import uuid4

from pydantic_ai.messages import ModelMessage, ModelRequest, ModelResponse, TextPart, UserPromptPart

from agent_hub.core.chat.events import (
    ErrorEvent,
    RunFinished,
    RunStarted,
    Source,
    StreamEvent,
    Token,
    ToolEnd,
)
from agent_hub.core.chat.titles import title_from_message
from agent_hub.core.errors import ErrorCode, HubError
from agent_hub.core.loop_engines.protocol import LoopEngine
from agent_hub.core.observability.tracer import Tracer
from agent_hub.core.registry.registry import AgentRegistry, CompiledAgent
from agent_hub.core.storage.repository import Repository


@dataclass
class ActiveRun:
    id: str
    conversation_id: str
    message_id: str
    queue: asyncio.Queue[StreamEvent | None] = field(default_factory=asyncio.Queue)
    task: asyncio.Task[None] | None = None
    started: asyncio.Event = field(default_factory=asyncio.Event)


class ChatService:
    def __init__(
        self,
        registry: AgentRegistry,
        repository: Repository,
        engine: Callable[[CompiledAgent], LoopEngine],
        tracer: Callable[[str], Tracer],
    ) -> None:
        self.registry, self.repository, self.engine, self.tracer = (
            registry,
            repository,
            engine,
            tracer,
        )
        self.runs: dict[str, ActiveRun] = {}
        self.lock = asyncio.Lock()

    async def start(
        self, name: str, message: str, conversation_id: str | None, enabled: bool, regenerate: bool
    ) -> ActiveRun:
        agent = self.registry.get(name)
        async with self.lock:
            if conversation_id and any(
                run.conversation_id == conversation_id for run in self.runs.values()
            ):
                raise HubError(
                    ErrorCode.CONFIG_INVALID, "A turn is already running in this conversation"
                )
            conversation, mid, content = await self.repository.prepare(
                name, conversation_id, message, title_from_message(message), regenerate
            )
            run = ActiveRun(str(uuid4()), conversation.id, mid)
            history: list[ModelMessage] = []
            limit = agent.definition.harness.history.max_messages
            previous = conversation.messages[:-2]
            for row in previous[-limit:] if limit else []:
                history.append(
                    ModelRequest(parts=[UserPromptPart(row.content)])
                    if row.role == "user"
                    else ModelResponse(parts=[TextPart(row.content)])
                )
            self.runs[run.id] = run
            run.queue.put_nowait(
                RunStarted(run_id=run.id, conversation_id=conversation.id, message_id=mid)
            )
            run.task = asyncio.create_task(self._produce(run, agent, content, history, enabled))
            return run

    async def _produce(
        self,
        run: ActiveRun,
        agent: CompiledAgent,
        message: str,
        history: list[ModelMessage],
        enabled: bool,
    ) -> None:
        run.started.set()
        started = time.monotonic()
        text = ""
        sources: dict[str, Source] = {}
        error_code: str | None = None
        finished = RunFinished(run_id=run.id, status="error", latency_ms=0)
        tracer = self.tracer(agent.definition.name)
        span = tracer.start_run(run.id, agent.definition.name)
        model_name = "unknown"
        try:
            engine = self.engine(agent)
            model = getattr(engine, "model", None)
            model_name = getattr(model, "model_name", "unknown")
            async for event in engine.stream(run.id, message, history, enabled):
                if isinstance(event, Token):
                    text += event.text
                elif isinstance(event, ToolEnd):
                    for source in event.sources:
                        sources[source.url] = source
                elif isinstance(event, ErrorEvent):
                    error_code = event.code
                    span.record_error(event.code)
                elif isinstance(event, RunFinished):
                    finished = event
                    continue
                run.queue.put_nowait(event)
        except asyncio.CancelledError:
            error_code = ErrorCode.RUN_CANCELLED
            finished.status = "stopped"
            run.queue.put_nowait(
                ErrorEvent(run_id=run.id, code=ErrorCode.RUN_CANCELLED, message="Response stopped")
            )
            span.record_error(ErrorCode.RUN_CANCELLED)
        except Exception:
            logging.getLogger(__name__).exception("run failed: %s", run.id)
            error_code = ErrorCode.MODEL_UNAVAILABLE
            run.queue.put_nowait(
                ErrorEvent(
                    run_id=run.id,
                    code=ErrorCode.MODEL_UNAVAILABLE,
                    message="Unable to complete this response",
                )
            )
            span.record_error(ErrorCode.MODEL_UNAVAILABLE)
        finally:
            finished.latency_ms = int((time.monotonic() - started) * 1000)
            await self.repository.finish(
                run.message_id,
                text,
                list(sources.values()),
                finished.status,
                error_code,
                model_name,
                finished.latency_ms,
                finished.tokens_in,
                finished.tokens_out,
            )
            span.end(
                input=message,
                output=text,
                latency_ms=finished.latency_ms,
                tokens_in=finished.tokens_in,
                tokens_out=finished.tokens_out,
                status=finished.status,
            )
            run.queue.put_nowait(finished)
            run.queue.put_nowait(None)
            self.runs.pop(run.id, None)

    async def stop(self, run_id: str) -> None:
        run = self.runs.get(run_id)
        if not run:
            raise HubError(ErrorCode.NOT_FOUND, "Active run not found")
        if run.task and not run.task.done():
            await run.started.wait()
            if not run.task.cancelling():
                run.task.cancel()
            await asyncio.shield(run.task)

    async def events(self, run: ActiveRun) -> AsyncIterator[StreamEvent]:
        try:
            while (event := await run.queue.get()) is not None:
                yield event
        finally:
            if run.task and not run.task.done():
                await run.started.wait()
                if not run.task.cancelling():
                    run.task.cancel()
                # Shield the producer's final SQLite write from client-disconnect cancellation.
                await asyncio.shield(run.task)

    async def close(self) -> None:
        await asyncio.gather(*(self.stop(key) for key in list(self.runs)), return_exceptions=True)
