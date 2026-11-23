"""Langfuse adapter imported only when configured and installed."""

from typing import Any

from agent_hub.core.observability.tracer import Span


class LangfuseSpan:
    def __init__(self, span: Any, include_content: bool) -> None:
        self.span = span
        self.include_content = include_content

    def end(self, **attributes: Any) -> None:
        if not self.include_content:
            attributes.pop("input", None)
            attributes.pop("output", None)
        self.span.update(**attributes)
        self.span.end()

    def record_error(self, error: str) -> None:
        self.span.update(level="ERROR", status_message=error)


class LangfuseTracer:
    enabled = True

    def __init__(self, public_key: str, secret_key: str, host: str, include_content: bool) -> None:
        from langfuse import Langfuse

        self.client = Langfuse(public_key=public_key, secret_key=secret_key, base_url=host)
        self.include_content = include_content
        self.roots: dict[str, Any] = {}

    def start_run(self, run_id: str, agent: str) -> Span:
        span = self.client.start_span(name="run", metadata={"run_id": run_id, "agent": agent})
        span.update_trace(session_id=run_id)
        self.roots[run_id] = span
        return LangfuseSpan(span, self.include_content)

    def start_span(self, name: str, run_id: str, **attributes: Any) -> Span:
        if not self.include_content:
            attributes.pop("input", None)
            attributes.pop("output", None)
        parent = self.roots.get(run_id, self.client)
        return LangfuseSpan(
            parent.start_span(name=name, metadata={"run_id": run_id}, **attributes),
            self.include_content,
        )
