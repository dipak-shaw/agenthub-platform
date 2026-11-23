"""Missing optional tracing configuration must never prevent serving traffic."""

import logging
from typing import Any

from agent_hub.core.observability.tracer import NoopTracer, Span, Tracer
from agent_hub.core.registry.definition import TracingConfig
from agent_hub.core.settings import Settings


class MultiSpan:
    def __init__(self, spans: list[Span]) -> None:
        self.spans = spans

    def end(self, **attributes: Any) -> None:
        for span in self.spans:
            try:
                span.end(**attributes)
            except Exception:
                logging.getLogger(__name__).debug("tracing export failed")

    def record_error(self, error: str) -> None:
        for span in self.spans:
            try:
                span.record_error(error)
            except Exception:
                pass


class SafeTracer:
    enabled = True

    def __init__(self, tracers: list[Tracer]) -> None:
        self.tracers = tracers

    def start_run(self, run_id: str, agent: str) -> Span:
        spans: list[Span] = []
        for tracer in self.tracers:
            try:
                spans.append(tracer.start_run(run_id, agent))
            except Exception:
                pass
        return MultiSpan(spans)

    def start_span(self, name: str, run_id: str, **attributes: Any) -> Span:
        spans: list[Span] = []
        for tracer in self.tracers:
            try:
                spans.append(tracer.start_span(name, run_id, **attributes))
            except Exception:
                pass
        return MultiSpan(spans)


def build_tracer(settings: Settings, config: TracingConfig | None = None) -> Tracer:
    tracers: list[Tracer] = []
    public = (config.public_key if config else "") or settings.langfuse_public_key
    secret = (
        config.secret_key if config else ""
    ) or settings.langfuse_secret_key.get_secret_value()
    host = (config.host if config else "") or settings.langfuse_host
    if public and secret:
        try:
            from agent_hub.core.observability.langfuse_tracer import LangfuseTracer

            tracers.append(LangfuseTracer(public, secret, host, settings.trace_include_content))
        except Exception:
            pass
    if settings.otel_exporter_otlp_endpoint:
        try:
            from agent_hub.core.observability.otel_tracer import OtelTracer

            tracers.append(OtelTracer(settings.otel_exporter_otlp_endpoint))
        except Exception:
            pass
    if not tracers:
        logging.getLogger(__name__).info("tracing: off")
        return NoopTracer()
    return SafeTracer(tracers)
