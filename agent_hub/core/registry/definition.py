"""The complete, closed agent.yaml contract."""

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid")


Nonempty = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class PromptFile(Contract):
    file: Nonempty


class ModelConfig(Contract):
    deployment: Nonempty = "default"
    temperature: float = Field(default=0.4, ge=0, le=2)
    max_output_tokens: int = Field(default=1200, gt=0, le=128000)


class LoopConfig(Contract):
    type: str = "basic"
    max_iterations: int = Field(gt=0, le=100)
    timeout_seconds: float = Field(gt=0, le=3600)


class HistoryConfig(Contract):
    max_messages: int = Field(default=20, ge=0, le=1000)


class Harness(Contract):
    system_prompt: PromptFile | Nonempty
    dynamic_system_prompts: list[Literal["today"]] = Field(default_factory=list)
    model: ModelConfig = Field(default_factory=ModelConfig)
    loop: LoopConfig
    history: HistoryConfig = Field(default_factory=HistoryConfig)


class SearchConfig(Contract):
    max_results: int = Field(default=5, gt=0, le=10)


class FetchConfig(Contract):
    max_chars: int = Field(default=8000, gt=0, le=100000)


class SearchTool(Contract):
    native: Literal["web_search"]
    config: SearchConfig = Field(default_factory=SearchConfig)
    user_toggle: bool = False


class FetchTool(Contract):
    native: Literal["fetch_page"]
    config: FetchConfig = Field(default_factory=FetchConfig)
    user_toggle: Literal[False] = False


ToolDefinition = Annotated[SearchTool | FetchTool, Field(discriminator="native")]


class TracingConfig(Contract):
    type: Literal["langfuse"] = "langfuse"
    public_key: str = ""
    secret_key: str = ""
    host: str = ""


class RuntimeConfig(Contract):
    tracing: TracingConfig | None = None


class AgentDefinition(Contract):
    name: Annotated[str, StringConstraints(pattern=r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")]
    display_name: Nonempty
    description: Nonempty
    avatar: Nonempty = "💬"
    accent_color: Annotated[str, StringConstraints(pattern=r"^#[0-9a-fA-F]{6}$")] = "#6366f1"
    tags: list[Nonempty] = Field(default_factory=list)
    starter_prompts: list[Nonempty] = Field(default_factory=list, max_length=4)
    harness: Harness
    tools: list[ToolDefinition] = Field(default_factory=list)
    runtime: RuntimeConfig = Field(default_factory=RuntimeConfig)
