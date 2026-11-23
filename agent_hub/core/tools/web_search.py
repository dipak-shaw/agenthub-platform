"""Bounded web search with deduplicated public HTTP sources."""

import asyncio
from typing import Any
from urllib.parse import urlsplit

from agent_hub.core.errors import ErrorCode, HubError
from agent_hub.core.settings import Settings
from agent_hub.core.tools.base import SearchProvider, SearchResult
from agent_hub.core.tools.search_providers.duckduckgo import DuckDuckGoSearch
from agent_hub.core.tools.search_providers.fake import FakeSearch
from agent_hub.core.tools.search_providers.tavily import TavilySearch


def search_provider(settings: Settings, demo: bool = False) -> SearchProvider:
    if demo or settings.app_mode == "offline" or settings.search_provider == "fake":
        return FakeSearch()
    if settings.search_provider == "tavily":
        key = settings.tavily_api_key.get_secret_value()
        if not key:
            raise HubError(ErrorCode.TOOL_FAILED, "TAVILY_API_KEY is not configured")
        return TavilySearch(key)
    return DuckDuckGoSearch()


class WebSearch:
    name = "web_search"

    def __init__(self, provider: SearchProvider, limit: int = 5) -> None:
        self.provider = provider
        self.limit = min(10, max(1, limit))

    async def search(self, query: str, max_results: int | None = None) -> list[SearchResult]:
        limit = min(self.limit, max(1, max_results or self.limit))
        try:
            async with asyncio.timeout(10):
                rows = await self.provider.search(query, limit)
        except Exception as exc:
            raise HubError(ErrorCode.TOOL_FAILED, "Web search failed or timed out") from exc
        seen: set[str] = set()
        result: list[SearchResult] = []
        for row in rows:
            if row.url not in seen and urlsplit(row.url).scheme in {"http", "https"}:
                seen.add(row.url)
                result.append(row)
        return result[:limit]

    async def invoke(self, arguments: dict[str, Any]) -> Any:
        return [row.model_dump() for row in await self.search(**arguments)]
