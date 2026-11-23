"""Offline streaming, retry taxonomy, and request budget tests."""

import asyncio

import httpx
import pytest
from pydantic_ai.exceptions import ModelHTTPError
from pydantic_ai.messages import ModelResponse, TextPart
from pydantic_ai.models import ModelRequestParameters
from pydantic_ai.models.function import FunctionModel

from agent_hub.core.errors import ErrorCode, HubError
from agent_hub.core.loop_engines.basic import BasicEngine
from agent_hub.core.models.foundry import foundry_model
from agent_hub.core.models.provider import build_model
from agent_hub.core.models.retry import RetryModel, retry_call, retry_delay, retryable
from agent_hub.core.settings import Settings
from agent_hub.core.testing import FakeClock, fixture_agent, scripted_model


async def test_retry_sequence():
    clock = FakeClock()
    attempt = 0

    async def call():
        nonlocal attempt
        attempt += 1
        if attempt == 1:
            raise httpx.HTTPStatusError(
                "rate",
                request=httpx.Request("GET", "https://fictional.example"),
                response=httpx.Response(429, headers={"Retry-After": "2"}),
            )
        if attempt == 2:
            raise TimeoutError()
        return "ok"

    assert await retry_call(call, clock.sleep, lambda: 0) == "ok"
    assert clock.sleeps == [2, 1]


@pytest.mark.parametrize(
    "error",
    [
        ValueError("invalid"),
        ModelHTTPError(401, "test"),
        ModelHTTPError(403, "test"),
        HubError(ErrorCode.TOOL_FAILED, "invalid arguments"),
    ],
)
async def test_no_retry(error):
    clock = FakeClock()

    async def call():
        raise error

    with pytest.raises(type(error)):
        await retry_call(call, clock.sleep)
    assert clock.sleeps == []


async def test_retry_exhaustion_and_cancel():
    clock = FakeClock()

    async def call():
        raise ModelHTTPError(503, "test")

    with pytest.raises(ModelHTTPError):
        await retry_call(call, clock.sleep, lambda: 0)
    assert clock.sleeps == [0.5, 1]

    async def cancelled():
        raise asyncio.CancelledError()

    with pytest.raises(asyncio.CancelledError):
        await retry_call(cancelled, clock.sleep)
    assert retryable(httpx.ConnectError("offline"))
    assert not retryable(ModelHTTPError(400, "test"))
    for value in ["bad", "Wed, 21 Oct 2015 07:28:00 GMT"]:
        error = httpx.HTTPStatusError(
            "x",
            request=httpx.Request("GET", "https://fictional.example"),
            response=httpx.Response(429, headers={"retry-after": value}),
        )
        assert retry_delay(error, 0, lambda: 0) >= 0


async def test_retry_wrapper():
    async def response(messages, info):
        return ModelResponse(parts=[TextPart("ok")])

    model = RetryModel(FunctionModel(response))
    assert (await model.request([], None, ModelRequestParameters())).parts[0].content == "ok"
    streamed = RetryModel(scripted_model(["hi"]))
    events = [
        event
        async for event in BasicEngine(fixture_agent(), Settings(_env_file=None), streamed).stream(
            "r", "hello", []
        )
    ]
    assert events[-1].status == "complete"
    broken = RetryModel(scripted_model(["partial"], error=ValueError("broken")))
    events = [
        event
        async for event in BasicEngine(fixture_agent(), Settings(_env_file=None), broken).stream(
            "r", "hello", []
        )
    ]
    assert events[-1].status == "error"
    assert "".join(e.text for e in events if e.type == "token") == "partial"


async def test_exact_plain_events(settings):
    events = [
        event
        async for event in BasicEngine(
            fixture_agent(), settings, scripted_model(["hello", " world"])
        ).stream("run", "hi", [])
    ]
    assert [e.type for e in events] == ["token", "token", "run_finished"]
    assert "".join(e.text for e in events[:-1]) == "hello world"
    assert events[-1].tokens_out > 0


async def test_tools_and_toggle(settings):
    agent = fixture_agent(tools=[{"native": "web_search", "user_toggle": True}])
    engine = BasicEngine(agent, settings)
    events = [e async for e in engine.stream("r", "search latest", [])]
    assert [e.type for e in events[:2]] == ["tool_start", "tool_end"]
    assert events[1].sources[0].index == 1
    assert "[1]" in "".join(e.text for e in events if e.type == "token")
    events = [e async for e in engine.stream("r", "search latest", [], False)]
    assert all(not e.type.startswith("tool") for e in events)
    assert events[-1].status == "complete"


async def test_timeout_cancel_and_limit(settings):
    agent = fixture_agent()
    agent.definition.harness.loop.timeout_seconds = 0.03
    events = [
        e
        async for e in BasicEngine(agent, settings, scripted_model(["part", "later"], 0.02)).stream(
            "r", "hi", []
        )
    ]
    assert [e.type for e in events] == ["token", "error", "run_finished"]
    assert events[-2].code == ErrorCode.RUN_TIMEOUT
    agent.definition.harness.loop.timeout_seconds = 5
    stream = BasicEngine(agent, settings, scripted_model(["later"], 5)).stream("r", "hi", [])
    task = asyncio.create_task(anext(stream))
    await asyncio.sleep(0.01)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    agent = fixture_agent(tools=[{"native": "web_search"}])
    agent.definition.harness.loop.max_iterations = 1
    events = [e async for e in BasicEngine(agent, settings).stream("r", "news", [])]
    assert events[-2].code == ErrorCode.RUN_TIMEOUT


@pytest.mark.parametrize(
    "error,code",
    [
        (ModelHTTPError(429, "x"), ErrorCode.MODEL_RATE_LIMITED),
        (HubError(ErrorCode.TOOL_FAILED, "tool failed"), ErrorCode.TOOL_FAILED),
    ],
)
async def test_error_code(settings, error, code):
    events = [
        e
        async for e in BasicEngine(
            fixture_agent(), settings, scripted_model(["partial"], error=error)
        ).stream("r", "hi", [])
    ]
    assert events[-2].code == code


def test_foundry_provider(settings):
    assert build_model(settings).model_name == "offline-demo"
    online = Settings(
        _env_file=None,
        azure_foundry_endpoint="https://fictional.example",
        azure_foundry_deployment="test",
        azure_foundry_api_key="fictional",
    )
    model = foundry_model(online, "default")
    assert model.model_name == "test"
    assert isinstance(build_model(online), RetryModel)
    online.azure_foundry_api_key = ""
    with pytest.raises((HubError, AttributeError)):
        foundry_model(online, "default")
