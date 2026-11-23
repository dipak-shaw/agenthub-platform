"""Typed native tools and an explicit tool registry."""

from typing import Any, Protocol

from pydantic import BaseModel


class SearchResult(BaseModel):
    title: str
    url: str
    snippet: str


class PageText(BaseModel):
    title: str
    text: str
    url: str


class NativeTool(Protocol):
    name: str

    async def invoke(self, arguments: dict[str, Any]) -> Any: ...


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, NativeTool] = {}

    def register(self, tool: NativeTool) -> None:
        if tool.name in self._tools:
            raise ValueError(f"Duplicate tool: {tool.name}")
        self._tools[tool.name] = tool

    def get(self, name: str) -> NativeTool:
        return self._tools[name]


class SearchProvider(Protocol):
    async def search(self, query: str, max_results: int) -> list[SearchResult]: ...
