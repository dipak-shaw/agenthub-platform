"""Load YAML and confine referenced files to their agent directory."""

import logging
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]
from pydantic import ValidationError

from agent_hub.core.errors import ConfigError
from agent_hub.core.registry.definition import AgentDefinition, PromptFile
from agent_hub.core.registry.registry import CompiledAgent
from agent_hub.core.secrets import resolve

logger = logging.getLogger(__name__)


def local_file(folder: Path, value: str, field: str) -> Path:
    result = (folder / value).resolve()
    if not result.is_relative_to(folder.resolve()) or not result.is_file():
        raise ConfigError(str(folder / "agent.yaml"), field, "file must exist inside agent folder")
    return result


def load(path: Path) -> CompiledAgent:
    try:
        raw: Any = yaml.safe_load(path.read_text(encoding="utf-8"))
        definition = AgentDefinition.model_validate(raw)
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        raise ConfigError(str(path), "$", "cannot read valid YAML") from exc
    except ValidationError as exc:
        details = "; ".join(
            f"{'.'.join(map(str, e['loc']))}: {e['msg']}" for e in exc.errors(include_input=False)
        )
        raise ConfigError(str(path), "$", details) from exc
    prompt_config = definition.harness.system_prompt
    prompt = (
        local_file(path.parent, prompt_config.file, "harness.system_prompt.file").read_text()
        if isinstance(prompt_config, PromptFile)
        else prompt_config
    )
    avatar = None
    if "/" in definition.avatar or "." in definition.avatar:
        avatar = local_file(path.parent, definition.avatar, "avatar")
        if avatar.suffix.lower() not in {".png", ".svg"}:
            raise ConfigError(str(path), "avatar", "only SVG or PNG files are supported")
    tracing = definition.runtime.tracing
    if tracing:
        try:
            for field in ("public_key", "secret_key", "host"):
                setattr(
                    tracing,
                    field,
                    resolve(getattr(tracing, field), str(path), f"runtime.tracing.{field}"),
                )
        except ConfigError:
            definition.runtime.tracing = None
            logger.info(
                "%s: runtime.tracing: disabled; optional environment reference is missing", path
            )
    return CompiledAgent(definition, prompt, path.parent, avatar)
