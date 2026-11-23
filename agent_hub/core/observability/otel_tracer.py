"""OTLP metadata-only telemetry, loaded only when configured."""

from typing import Any

from agent_hub.core.observability.tracer import Span


class OtelSpan:
    def __init__(self, span: Any) -> None:
        self.span = span

    def end(self, **attributes: Any) -> None:
        # Never export content through the infrastructure telemetry channel.
        for key in ("latency_ms", "tokens_in", "tokens_out", "status", "model"):
            if key in attributes:
                self.span.set_attribute(key, attributes[key])
        self.span.end()

    def record_error(self, error: str) -> None:
        self.span.set_attribute("error_code", error)


class OtelTracer:
    enabled = True

    def __init__(self, endpoint: str) -> None:
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor

        self.provider = TracerProvider()
        self.provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=endpoint)))
        self.tracer = self.provider.get_tracer("agent_hub")
        self.roots: dict[str, Any] = {}

    def start_run(self, run_id: str, agent: str) -> Span:
        span = self.tracer.start_span("run", attributes={"run_id": run_id, "agent": agent})
        self.roots[run_id] = span
        return OtelSpan(span)

    def start_span(self, name: str, run_id: str, **attributes: Any) -> Span:
        from opentelemetry.trace import set_span_in_context

        root = self.roots.get(run_id)
        context = set_span_in_context(root) if root else None
        return OtelSpan(
            self.tracer.start_span(name, context=context, attributes={"run_id": run_id})
        )
