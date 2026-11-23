"""Stable failure codes shared by HTTP, streaming, and CLI clients."""

from enum import StrEnum


class ErrorCode(StrEnum):
    CONFIG_INVALID = "config_invalid"
    MODEL_UNAVAILABLE = "model_unavailable"
    MODEL_RATE_LIMITED = "model_rate_limited"
    TOOL_FAILED = "tool_failed"
    RUN_TIMEOUT = "run_timeout"
    RUN_CANCELLED = "run_cancelled"
    NOT_FOUND = "not_found"


class HubError(Exception):
    """An actionable error safe to return to a client."""

    def __init__(self, code: ErrorCode, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(message)


class ConfigError(HubError):
    """Configuration errors always identify their source and field."""

    def __init__(self, file: str, field: str, detail: str) -> None:
        super().__init__(ErrorCode.CONFIG_INVALID, f"{file}: {field}: {detail}")
