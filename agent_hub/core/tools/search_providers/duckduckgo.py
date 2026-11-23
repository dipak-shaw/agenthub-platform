"""Run the synchronous DDGS client off the event loop."""

import asyncio

from ddgs import DDGS

from agent_hub.core.tools.base import SearchResult


class DuckDuckGoSearch:
    async def search(self, query: str, max_results: int) -> list[SearchResult]:
        def lookup() -> list[SearchResult]:
            with DDGS(timeout=10) as client:
                return [
                    SearchResult(title=row["title"], url=row["href"], snippet=row["body"])
                    for row in client.text(query, max_results=max_results)
                ]

        return await asyncio.to_thread(lookup)
