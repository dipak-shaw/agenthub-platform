"""Async SQLite engine lifecycle with foreign keys and a bounded busy timeout."""

from pathlib import Path
from typing import Any

from sqlalchemy import event
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from agent_hub.core.storage.tables import Base


def create_database(url: str) -> AsyncEngine:
    parsed = make_url(url)
    if parsed.drivername != "sqlite+aiosqlite":
        raise ValueError("DATABASE_URL must use sqlite+aiosqlite")
    if parsed.database and parsed.database != ":memory:":
        Path(parsed.database).parent.mkdir(parents=True, exist_ok=True)
    engine = create_async_engine(url)

    @event.listens_for(engine.sync_engine, "connect")
    def configure(connection: Any, _: Any) -> None:
        cursor = connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA busy_timeout=5000")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.close()

    return engine


async def initialize(engine: AsyncEngine) -> None:
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
