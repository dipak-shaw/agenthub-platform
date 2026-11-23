"""Tavily HTTP adapter; the key is never included in tool events."""

import httpx

from agent_hub.core.tools.base import SearchResult


class TavilySearch:
    def __init__(self, key: str) -> None:
        self.key = key

    async def search(self, query: str, max_results: int) -> list[SearchResult]:
        async with httpx.AsyncClient(timeout=10, trust_env=False) as client:
            response = await client.post(
                "https://api.tavily.com/search",
                json={
                    "api_key": self.key,
                    "query": query,
                    "max_results": max_results,
                },
            )
            response.raise_for_status()
            return [
                SearchResult(title=row["title"], url=row["url"], snippet=row.get("content", ""))
                for row in response.json()["results"]
            ]
