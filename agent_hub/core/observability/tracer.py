"""Small telemetry contracts independent of optional SDKs."""

from typing import Any, Protocol


class Span(Protocol):
    def end(self, **attributes: Any) -> None: ...
    def record_error(self, error: str) -> None: ...


class Tracer(Protocol):
    enabled: bool

    def start_run(self, run_id: str, agent: str) -> Span: ...
    def start_span(self, name: str, run_id: str, **attributes: Any) -> Span: ...


class NoopSpan:
    def end(self, **attributes: Any) -> None:
        pass

    def record_error(self, error: str) -> None:
        pass


class NoopTracer:
    enabled = False

    def start_run(self, run_id: str, agent: str) -> Span:
        return NoopSpan()

    def start_span(self, name: str, run_id: str, **attributes: Any) -> Span:
        return NoopSpan()
