"""Optional tracing is lazy, best effort, and enforces the content ceiling."""

import builtins
import sys
from types import SimpleNamespace
from unittest.mock import MagicMock

from agent_hub.core.loop_engines.basic import BasicEngine
from agent_hub.core.observability.factory import SafeTracer, build_tracer
from agent_hub.core.observability.langfuse_tracer import LangfuseSpan, LangfuseTracer
from agent_hub.core.observability.otel_tracer import OtelSpan, OtelTracer
from agent_hub.core.observability.tracer import NoopTracer
from agent_hub.core.settings import Settings
from agent_hub.core.testing import fixture_agent


def test_no_configuration(caplog):
    with caplog.at_level("INFO"):
        tracer = build_tracer(Settings(_env_file=None))
    assert isinstance(tracer, NoopTracer)
    assert caplog.text.count("tracing: off") == 1
    tracer.start_run("r", "a").end()
    tracer.start_span("tool_call", "r").record_error("tool_failed")


def test_missing_optional_packages(monkeypatch):
    real_import = builtins.__import__

    def missing(name, *args, **kwargs):
        if name.startswith(("langfuse", "opentelemetry")):
            raise ImportError("optional package absent")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", missing)
    settings = Settings(
        _env_file=None,
        langfuse_public_key="fictional",
        langfuse_secret_key="fictional",
        otel_exporter_otlp_endpoint="http://localhost:4318/v1/traces",
    )
    assert not build_tracer(settings).enabled


def test_langfuse_content_and_session(monkeypatch):
    client = MagicMock()
    monkeypatch.setitem(
        sys.modules, "langfuse", SimpleNamespace(Langfuse=MagicMock(return_value=client))
    )
    tracer = LangfuseTracer("fictional", "fictional", "http://localhost", False)
    run = tracer.start_run("run-1", "fixture")
    client.start_span.return_value.update_trace.assert_called_once_with(session_id="run-1")
    run.end(input="private", output="private", status="complete")
    assert "private" not in str(client.start_span.return_value.update.call_args)
    span = tracer.start_span("model_call", "run-1", input="private")
    span.record_error("model_unavailable")
    span.end(output="private")
    assert "private" not in str(client.mock_calls)
    direct = LangfuseSpan(MagicMock(), True)
    direct.end(input="visible")
    direct.span.update.assert_called_with(input="visible")
    assert build_tracer(
        Settings(_env_file=None, langfuse_public_key="fictional", langfuse_secret_key="fictional")
    ).enabled


def test_otel_never_content(monkeypatch):
    span = MagicMock()
    adapter = OtelSpan(span)
    adapter.end(input="private", output="private", latency_ms=3, tokens_in=2, model="test")
    adapter.record_error("tool_failed")
    assert "private" not in str(span.mock_calls)
    provider = MagicMock()
    monkeypatch.setitem(
        sys.modules, "opentelemetry.sdk.trace", SimpleNamespace(TracerProvider=lambda: provider)
    )
    monkeypatch.setitem(
        sys.modules,
        "opentelemetry.sdk.trace.export",
        SimpleNamespace(BatchSpanProcessor=lambda x: x),
    )
    monkeypatch.setitem(
        sys.modules,
        "opentelemetry.exporter.otlp.proto.http.trace_exporter",
        SimpleNamespace(OTLPSpanExporter=lambda **kw: object()),
    )
    monkeypatch.setitem(
        sys.modules, "opentelemetry.trace", SimpleNamespace(set_span_in_context=lambda x: x)
    )
    tracer = OtelTracer("http://localhost")
    tracer.start_run("r", "a").end()
    tracer.start_span("model_call", "r", input="private").end()
    assert "private" not in str(provider.mock_calls)
    assert build_tracer(
        Settings(_env_file=None, otel_exporter_otlp_endpoint="http://localhost")
    ).enabled


def test_tracer_failure_is_not_request_failure():
    broken = MagicMock()
    broken.start_run.side_effect = ValueError()
    broken.start_span.side_effect = ValueError()
    safe = SafeTracer([broken])
    safe.start_run("r", "a").end()
    safe.start_span("tool_call", "r").record_error("tool_failed")
    broken = MagicMock()
    broken.start_run.return_value.end.side_effect = ValueError()
    broken.start_run.return_value.record_error.side_effect = ValueError()
    span = SafeTracer([broken]).start_run("r", "a")
    span.record_error("tool_failed")
    span.end()


async def test_in_memory_span_tree(settings):
    calls = []

    class Span:
        def __init__(self, name):
            self.name = name

        def end(self, **kwargs):
            calls.append(("end", self.name))

        def record_error(self, error):
            calls.append(("error", error))

    class Tracer:
        enabled = True

        def start_run(self, run_id, agent):
            calls.append(("run", run_id))
            return Span("run")

        def start_span(self, name, run_id, **attributes):
            calls.append((name, run_id))
            return Span(name)

    tracer = Tracer()
    tracer.start_run("same-id", "fixture")
    engine = BasicEngine(fixture_agent(tools=[{"native": "web_search"}]), settings, tracer=tracer)
    events = [event async for event in engine.stream("same-id", "search news", [])]
    assert events[-1].status == "complete"
    assert ("model_call", "same-id") in calls and ("tool_call", "same-id") in calls
