"""Repository boundary; each write is committed before events are published."""

import builtins
import json
from typing import Protocol

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker

from agent_hub.core.chat.events import Source
from agent_hub.core.errors import ErrorCode, HubError
from agent_hub.core.storage.tables import (
    Conversation,
    ConversationDetail,
    ConversationRecord,
    Message,
    MessageRecord,
    identifier,
    now,
)


class Repository(Protocol):
    async def list(self, agent: str | None = None) -> builtins.list[ConversationRecord]: ...
    async def get(self, conversation_id: str) -> ConversationDetail: ...
    async def rename(self, conversation_id: str, title: str) -> ConversationRecord: ...
    async def delete(self, conversation_id: str) -> None: ...
    async def prepare(
        self, agent: str, conversation_id: str | None, content: str, title: str, regenerate: bool
    ) -> tuple[ConversationDetail, str, str]: ...
    async def finish(
        self,
        message_id: str,
        content: str,
        sources: builtins.list[Source],
        status: str,
        error_code: str | None,
        model: str,
        latency_ms: int,
        tokens_in: int,
        tokens_out: int,
    ) -> None: ...


class SQLiteRepository:
    def __init__(self, engine: AsyncEngine) -> None:
        self.sessions = async_sessionmaker(engine, expire_on_commit=False)

    async def list(self, agent: str | None = None) -> builtins.list[ConversationRecord]:
        async with self.sessions() as session:
            query = select(Conversation).order_by(Conversation.updated_at.desc())
            if agent:
                query = query.where(Conversation.agent_name == agent)
            return [ConversationRecord.model_validate(row) for row in await session.scalars(query)]

    async def get(self, conversation_id: str) -> ConversationDetail:
        async with self.sessions() as session:
            row = await session.get(Conversation, conversation_id)
            if not row:
                raise HubError(ErrorCode.NOT_FOUND, "Conversation not found")
            messages = await session.scalars(
                select(Message)
                .where(Message.conversation_id == conversation_id)
                .order_by(Message.created_at, Message.id)
            )
            records = []
            for message in messages:
                record = MessageRecord.model_validate(message)
                record.sources = [
                    Source.model_validate(item) for item in json.loads(message.sources_json)
                ]
                records.append(record)
            return ConversationDetail(
                **ConversationRecord.model_validate(row).model_dump(), messages=records
            )

    async def rename(self, conversation_id: str, title: str) -> ConversationRecord:
        async with self.sessions.begin() as session:
            row = await session.get(Conversation, conversation_id)
            if not row:
                raise HubError(ErrorCode.NOT_FOUND, "Conversation not found")
            row.title, row.updated_at = title, now()
            return ConversationRecord.model_validate(row)

    async def delete(self, conversation_id: str) -> None:
        async with self.sessions.begin() as session:
            row = await session.get(Conversation, conversation_id)
            if not row:
                raise HubError(ErrorCode.NOT_FOUND, "Conversation not found")
            await session.delete(row)

    async def prepare(
        self, agent: str, conversation_id: str | None, content: str, title: str, regenerate: bool
    ) -> tuple[ConversationDetail, str, str]:
        async with self.sessions.begin() as session:
            if conversation_id:
                conversation = await session.get(Conversation, conversation_id)
                if not conversation or conversation.agent_name != agent:
                    raise HubError(ErrorCode.NOT_FOUND, "Conversation not found for this agent")
            else:
                if regenerate:
                    raise HubError(
                        ErrorCode.NOT_FOUND, "Regeneration needs an existing conversation"
                    )
                conversation = Conversation(id=identifier(), agent_name=agent, title=title)
                session.add(conversation)
                await session.flush()
            if regenerate:
                previous = list(
                    await session.scalars(
                        select(Message)
                        .where(Message.conversation_id == conversation.id)
                        .order_by(Message.created_at.desc(), Message.id.desc())
                    )
                )
                if (
                    len(previous) < 2
                    or previous[0].role != "assistant"
                    or previous[1].role != "user"
                ):
                    raise HubError(ErrorCode.NOT_FOUND, "No assistant response to regenerate")
                content = previous[1].content
                await session.execute(delete(Message).where(Message.id == previous[0].id))
            else:
                session.add(Message(conversation_id=conversation.id, role="user", content=content))
                await session.flush()
            message_id = identifier()
            session.add(
                Message(
                    id=message_id,
                    conversation_id=conversation.id,
                    role="assistant",
                    status="stopped",
                    error_code="run_cancelled",
                )
            )
            conversation.updated_at = now()
            cid = conversation.id
        return await self.get(cid), message_id, content

    async def finish(
        self,
        message_id: str,
        content: str,
        sources: builtins.list[Source],
        status: str,
        error_code: str | None,
        model: str,
        latency_ms: int,
        tokens_in: int,
        tokens_out: int,
    ) -> None:
        async with self.sessions.begin() as session:
            row = await session.get(Message, message_id)
            if not row:
                return
            row.content, row.status, row.error_code = content, status, error_code
            row.sources_json = json.dumps([source.model_dump() for source in sources])
            row.model, row.latency_ms = model, latency_ms
            row.tokens_in, row.tokens_out = tokens_in, tokens_out
            conversation = await session.get(Conversation, row.conversation_id)
            if conversation:
                conversation.updated_at = now()
