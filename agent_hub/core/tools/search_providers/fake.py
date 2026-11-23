"""Fictional deterministic search results; never accesses the network."""

from agent_hub.core.tools.base import SearchResult


class FakeSearch:
    async def search(self, query: str, max_results: int) -> list[SearchResult]:
        return [
            SearchResult(
                title="Lumen Research Notes",
                url="https://lumen.example/notes",
                snippet="A fictional research team compares transparent, testable AI systems.",
            ),
            SearchResult(
                title="Orchard Learning Journal",
                url="https://orchard.example/journal",
                snippet="A fictional guide recommends small experiments and reliable sources.",
            ),
        ][:max_results]
