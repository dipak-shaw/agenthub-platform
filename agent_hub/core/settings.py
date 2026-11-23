"""Environment settings with an offline, key-free default."""

from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_mode: Literal["auto", "offline"] = "auto"
    agents_dir: Path = Path("agent_hub/agents")
    database_url: str = "sqlite+aiosqlite:///./data/agent_hub.db"
    web_dist: Path = Path("web/dist")
    azure_foundry_endpoint: str = ""
    azure_foundry_deployment: str = ""
    azure_foundry_api_key: SecretStr = SecretStr("")
    azure_foundry_api_version: str = "2024-10-21"
    azure_foundry_auth: Literal["api_key", "entra_id"] = "api_key"
    search_provider: Literal["duckduckgo", "tavily", "fake"] = "duckduckgo"
    tavily_api_key: SecretStr = SecretStr("")
    langfuse_public_key: str = ""
    langfuse_secret_key: SecretStr = SecretStr("")
    langfuse_host: str = "https://cloud.langfuse.com"
    otel_exporter_otlp_endpoint: str = ""
    trace_include_content: bool = False
    max_message_chars: int = Field(default=16000, gt=0, le=100000)

    def is_demo(self, deployment: str = "default") -> bool:
        """An explicit agent deployment can override the environment default."""
        selected = self.azure_foundry_deployment if deployment == "default" else deployment
        return self.app_mode == "offline" or not (self.azure_foundry_endpoint and selected)

    @property
    def effective_search_provider(self) -> str:
        return "fake" if self.is_demo() else self.search_provider
