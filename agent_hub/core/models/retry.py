"""Bounded retries before streaming starts; partial responses are never replayed."""

import asyncio
import random
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from typing import Any

import httpx
from openai import APIConnectionError, APIStatusError
from pydantic_ai import RunContext
from pydantic_ai.exceptions import ModelHTTPError
from pydantic_ai.messages import ModelMessage, ModelResponse
from pydantic_ai.models import ModelRequestParameters, StreamedResponse
from pydantic_ai.models.wrapper import WrapperModel
from pydantic_ai.settings import ModelSettings


def retryable(error: Exception) -> bool:
    if isinstance(
        error, (TimeoutError, httpx.TimeoutException, httpx.NetworkError, APIConnectionError)
    ):
        return True
    if isinstance(error, (APIStatusError, ModelHTTPError, httpx.HTTPStatusError)):
        code = (
            error.response.status_code
            if isinstance(error, httpx.HTTPStatusError)
            else error.status_code
        )
        return code == 429 or 500 <= code < 600
    return False


def retry_delay(error: Exception, attempt: int, jitter: Callable[[], float]) -> float:
    response = getattr(error, "response", None)
    headers = getattr(response, "headers", {})
    raw = headers.get("retry-after")
    if raw:
        try:
            return max(0.0, float(raw))
        except ValueError:
            try:
                return max(0.0, (parsedate_to_datetime(raw) - datetime.now(UTC)).total_seconds())
            except (ValueError, TypeError):
                pass
    return float(0.5 * (2**attempt) + jitter() * 0.25)


async def retry_call[T](
    call: Callable[[], Awaitable[T]],
    sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
    jitter: Callable[[], float] = random.random,
) -> T:
    for attempt in range(3):
        try:
            return await call()
        except Exception as error:
            if attempt == 2 or not retryable(error):
                raise
            await sleep(retry_delay(error, attempt, jitter))
    raise AssertionError("unreachable")


class RetryModel(WrapperModel):
    async def request(
        self,
        messages: list[ModelMessage],
        model_settings: ModelSettings | None,
        model_request_parameters: ModelRequestParameters,
    ) -> ModelResponse:
        return await retry_call(
            lambda: self.wrapped.request(messages, model_settings, model_request_parameters)
        )

    @asynccontextmanager
    async def request_stream(
        self,
        messages: list[ModelMessage],
        model_settings: ModelSettings | None,
        model_request_parameters: ModelRequestParameters,
        run_context: RunContext[Any] | None = None,
    ) -> AsyncIterator[StreamedResponse]:
        # Retry only entering the provider context. Once yielded, no tokens may be replayed.
        context = self.wrapped.request_stream(
            messages, model_settings, model_request_parameters, run_context
        )

        async def enter() -> StreamedResponse:
            nonlocal context
            context = self.wrapped.request_stream(
                messages, model_settings, model_request_parameters, run_context
            )
            return await context.__aenter__()

        stream = await retry_call(enter)
        try:
            yield stream
        except BaseException as exc:
            if not await context.__aexit__(type(exc), exc, exc.__traceback__):
                raise
        else:
            await context.__aexit__(None, None, None)
