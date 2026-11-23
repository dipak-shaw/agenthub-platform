"""Deterministic, genuinely streamed offline FunctionModel."""

import asyncio
import json
from collections.abc import AsyncIterator

from pydantic_ai.messages import ModelMessage, ModelRequest, ToolReturnPart, UserPromptPart
from pydantic_ai.models.function import AgentInfo, DeltaToolCall, FunctionModel


async def demo_stream(
    messages: list[ModelMessage], info: AgentInfo
) -> AsyncIterator[str | dict[int, DeltaToolCall]]:
    query = ""
    returned: list[ToolReturnPart] = []
    for message in messages:
        if isinstance(message, ModelRequest):
            for part in message.parts:
                if isinstance(part, UserPromptPart):
                    query = str(part.content)
                    returned = []
                elif isinstance(part, ToolReturnPart):
                    returned.append(part)
    can_search = any(tool.name == "web_search" for tool in info.function_tools)
    wants_search = any(word in query.lower() for word in ("latest", "today", "news", "search"))
    if wants_search and can_search and not returned:
        yield {0: DeltaToolCall(name="web_search", json_args=json.dumps({"query": query}))}
        return
    if returned:
        content = returned[-1].content
        rows = content if isinstance(content, list) else []
        details = "\n".join(
            f"- {row.get('title', 'Source')}: {row.get('snippet', '')} [{index}]"
            for index, row in enumerate(rows, 1)
            if isinstance(row, dict)
        )
        answer = f"Here is what I found in the **fictional demo sources**:\n\n{details}"
    else:
        answer = (
            "## Let's explore that\n\nI'm running in **demo mode**, so this is a deterministic "
            "preview, not a live model answer.\n\n"
            "- Break your question into small parts.\n- Look for reliable evidence.\n"
            "- Compare what you find.\n\n"
            "Try asking for the latest news to see web search and citations."
        )
    for offset in range(0, len(answer), 12):
        await asyncio.sleep(0.015)
        yield answer[offset : offset + 12]


def demo_model() -> FunctionModel:
    return FunctionModel(stream_function=demo_stream, model_name="offline-demo")
