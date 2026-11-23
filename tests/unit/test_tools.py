"""HTTP and search tests never access the network."""

import asyncio
import socket
from unittest.mock import AsyncMock

import httpx
import pytest

from agent_hub.core.errors import HubError
from agent_hub.core.settings import Settings
from agent_hub.core.tools.base import SearchResult, ToolRegistry
from agent_hub.core.tools.fetch_page import MAX_BYTES, FetchPage, public_address
from agent_hub.core.tools.search_providers.duckduckgo import DuckDuckGoSearch
from agent_hub.core.tools.search_providers.fake import FakeSearch
from agent_hub.core.tools.search_providers.tavily import TavilySearch
from agent_hub.core.tools.web_search import WebSearch, search_provider


@pytest.mark.parametrize(
    "url",
    [
        "file:///etc/passwd",
        "ftp://host/file",
        "http://localhost",
        "http://a.localhost",
        "https://user:pass@public.example",
        "http://127.0.0.1",
        "http://10.0.0.1",
        "http://169.254.169.254",
        "http://[::1]",
        "http://[fc00::1]",
        "http://[::ffff:127.0.0.1]",
    ],
)
async def test_private_rejected(url, monkeypatch):
    async def resolve(*args, **kwargs):
        return [(socket.AF_INET, socket.SOCK_STREAM, 0, "", ("127.0.0.1", 80))]

    monkeypatch.setattr(asyncio.get_running_loop(), "getaddrinfo", resolve)
    with pytest.raises(HubError):
        await public_address(url)


async def test_public_resolver_and_mixed_dns(monkeypatch):
    loop = asyncio.get_running_loop()
    records = [(socket.AF_INET, socket.SOCK_STREAM, 0, "", ("93.184.216.34", 443))]
    monkeypatch.setattr(loop, "getaddrinfo", AsyncMock(return_value=records))
    assert await public_address("https://fictional.example") == (
        "fictional.example",
        "93.184.216.34",
    )
    records.append((socket.AF_INET, socket.SOCK_STREAM, 0, "", ("10.0.0.1", 443)))
    with pytest.raises(HubError):
        await public_address("https://fictional.example")


@pytest.fixture
async def public_dns(monkeypatch):
    async def lookup(*args, **kwargs):
        return [(socket.AF_INET, socket.SOCK_STREAM, 0, "", ("93.184.216.34", 443))]

    monkeypatch.setattr(asyncio.get_running_loop(), "getaddrinfo", lookup)


async def test_fetch_clean_and_pinned(respx_mock, public_dns):
    route = respx_mock.get("https://93.184.216.34/page").mock(
        return_value=httpx.Response(
            200,
            headers={"content-type": "text/html"},
            text=(
                "<title>Fictional</title><style>hidden</style>"
                "<main>Hello <b>world</b><script>bad()</script></main>"
            ),
        )
    )
    result = await FetchPage(5).invoke({"url": "https://fictional.example/page"})
    assert result == {
        "title": "Fictional",
        "text": "Hello",
        "url": "https://fictional.example/page",
    }
    request = route.calls[0].request
    assert request.headers["host"] == "fictional.example"
    assert request.extensions["sni_hostname"] == "fictional.example"


@pytest.mark.parametrize(
    "response",
    [
        httpx.Response(200, headers={"content-length": str(MAX_BYTES + 1)}),
        httpx.Response(200, content=b"a" * (MAX_BYTES + 1)),
        httpx.Response(200, headers={"content-type": "application/octet-stream"}),
        httpx.Response(500),
        httpx.Response(302, headers={"location": "http://localhost/secrets"}),
    ],
)
async def test_fetch_limits(response, respx_mock, public_dns):
    respx_mock.get("https://93.184.216.34/").mock(return_value=response)
    with pytest.raises(HubError):
        await FetchPage().fetch("https://fictional.example")


async def test_redirect_loop_and_timeout(respx_mock, public_dns):
    route = respx_mock.get("https://93.184.216.34/").mock(
        return_value=httpx.Response(302, headers={"location": "/"})
    )
    with pytest.raises(HubError, match="redirects"):
        await FetchPage().fetch("https://fictional.example")
    assert route.call_count == 6
    route.mock(side_effect=httpx.ReadTimeout("timeout"))
    with pytest.raises(HubError, match="timed out"):
        await FetchPage().fetch("https://fictional.example")


async def test_search_dedupe_cap_error_and_registry():
    row = SearchResult(title="Example", url="https://fictional.example", snippet="Fictional")
    provider = AsyncMock()
    provider.search.return_value = [
        row,
        row,
        SearchResult(title="bad", url="javascript:bad", snippet=""),
    ]
    search = WebSearch(provider, 99)
    assert await search.invoke({"query": "test", "max_results": 200}) == [row.model_dump()]
    provider.search.assert_awaited_once_with("test", 10)
    provider.search.side_effect = TimeoutError()
    with pytest.raises(HubError):
        await search.search("test")
    registry = ToolRegistry()
    registry.register(search)
    assert registry.get("web_search") is search
    with pytest.raises(ValueError):
        registry.register(search)


async def test_tavily(respx_mock):
    route = respx_mock.post("https://api.tavily.com/search").mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
                    {"title": "Fictional", "url": "https://example.test", "content": "notes"}
                ]
            },
        )
    )
    assert (await TavilySearch("fictional-key").search("query", 3))[0].snippet == "notes"
    assert b"fictional-key" in route.calls[0].request.content


async def test_ddgs(monkeypatch):
    class Client:
        def __init__(self, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def text(self, *args, **kwargs):
            return [{"title": "Fictional", "href": "https://example.test", "body": "notes"}]

    monkeypatch.setattr("agent_hub.core.tools.search_providers.duckduckgo.DDGS", Client)
    assert (await DuckDuckGoSearch().search("test", 2))[0].snippet == "notes"


def test_provider_selection():
    assert isinstance(search_provider(Settings(_env_file=None), True), FakeSearch)
    assert isinstance(search_provider(Settings(_env_file=None)), DuckDuckGoSearch)
    assert isinstance(
        search_provider(
            Settings(_env_file=None, search_provider="tavily", tavily_api_key="fictional")
        ),
        TavilySearch,
    )
    with pytest.raises(HubError):
        search_provider(Settings(_env_file=None, search_provider="tavily"))
