"""Every test uses temporary SQLite and offline models unless explicitly mocked."""

from pathlib import Path

import pytest

from agent_hub.core.settings import Settings


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    return Settings(
        _env_file=None,
        app_mode="offline",
        agents_dir=Path("tests/fixtures/agents"),
        database_url=f"sqlite+aiosqlite:///{tmp_path}/test.db",
    )
