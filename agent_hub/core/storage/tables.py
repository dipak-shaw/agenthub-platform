"""SQLite persistence models and API-facing typed records."""

from datetime import UTC, datetime
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict
from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from agent_hub.core.chat.events import Source


def now() -> str:
    return datetime.now(UTC).isoformat()


def identifier() -> str:
    return str(uuid4())


class Base(DeclarativeBase):
    pass


class Conversation(Base):
    __tablename__ = "conversations"
    id: Mapped[str] = mapped_column(primary_key=True, default=identifier)
    agent_name: Mapped[str] = mapped_column(index=True)
    title: Mapped[str] = mapped_column(String(60))
    created_at: Mapped[str] = mapped_column(default=now)
    updated_at: Mapped[str] = mapped_column(default=now, index=True)


class Message(Base):
    __tablename__ = "messages"
    id: Mapped[str] = mapped_column(primary_key=True, default=identifier)
    conversation_id: Mapped[str] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"), index=True
    )
    role: Mapped[str]
    content: Mapped[str] = mapped_column(Text, default="")
    sources_json: Mapped[str] = mapped_column(Text, default="[]")
    status: Mapped[str] = mapped_column(default="complete")
    error_code: Mapped[str | None]
    model: Mapped[str | None]
    latency_ms: Mapped[int] = mapped_column(default=0)
    tokens_in: Mapped[int] = mapped_column(default=0)
    tokens_out: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[str] = mapped_column(default=now)


class ConversationRecord(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    agent_name: str
    title: str
    created_at: str
    updated_at: str


class MessageRecord(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    conversation_id: str
    role: Literal["user", "assistant"]
    content: str
    sources: list[Source] = []
    status: Literal["complete", "stopped", "error"]
    error_code: str | None
    model: str | None
    latency_ms: int
    tokens_in: int
    tokens_out: int
    created_at: str


class ConversationDetail(ConversationRecord):
    messages: list[MessageRecord]
