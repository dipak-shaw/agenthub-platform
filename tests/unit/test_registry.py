"""Each invalid fixture must identify its file and offending config field."""

import shutil
from pathlib import Path

import pytest

from agent_hub.core.errors import ConfigError, HubError
from agent_hub.core.registry.compiler import compile_registry
from agent_hub.core.registry.loader import load
from agent_hub.core.secrets import resolve
from agent_hub.core.settings import Settings

BROKEN = Path("tests/fixtures/agents/broken")
FIELDS = {
    "unknown-root": "extra",
    "name-format": "name",
    "display-required": "display_name",
    "description-required": "description",
    "prompt-missing": "harness.system_prompt.file",
    "avatar-missing": "avatar",
    "tool-unknown": "tools",
    "tool-config": "tools",
    "tool-config-unknown": "tools",
    "engine-unknown": "harness.loop.type",
    "timeout-required": "timeout_seconds",
    "iterations-required": "max_iterations",
    "timeout-positive": "timeout_seconds",
    "iterations-positive": "max_iterations",
    "starters-limit": "starter_prompts",
    "accent-invalid": "accent_color",
    "unknown-nested": "harness.model",
    "prompt-traversal": "harness.system_prompt.file",
    "dynamic-unknown": "dynamic_system_prompts",
    "tracing-unknown": "runtime.tracing",
}


@pytest.mark.parametrize("fixture,field", FIELDS.items())
def test_invalid_fixture(fixture, field, tmp_path):
    source = BROKEN / fixture / "agent.yaml"
    dest = tmp_path / fixture
    dest.mkdir()
    shutil.copy(source, dest / "agent.yaml")
    with pytest.raises(ConfigError) as caught:
        compile_registry(tmp_path)
    assert str(dest / "agent.yaml") in str(caught.value)
    assert field in str(caught.value)


def test_duplicate_and_valid(tmp_path):
    src = Path("tests/fixtures/agents/plain-bot")
    shutil.copytree(src, tmp_path / "one")
    shutil.copytree(src, tmp_path / "two")
    with pytest.raises(ConfigError, match="name: duplicate"):
        compile_registry(tmp_path)
    registry = compile_registry(Path("tests/fixtures/agents"))
    assert len(registry.all()) == 2
    assert registry.get("plain-bot").system_prompt
    with pytest.raises(HubError):
        registry.get("missing")


def test_optional_tracing(tmp_path, monkeypatch, caplog):
    monkeypatch.delenv("MISSING_TEST_SECRET", raising=False)
    text = Path("tests/fixtures/agents/search-bot/agent.yaml").read_text()
    text = text.replace(
        "system_prompt:\n    file: prompts/system-prompt.md", "system_prompt: Hello"
    )
    text += "\nruntime:\n  tracing:\n    secret_key: os.environ/MISSING_TEST_SECRET\n"
    path = tmp_path / "agent.yaml"
    path.write_text(text)
    with caplog.at_level("INFO"):
        agent = load(path)
    assert agent.definition.runtime.tracing is None
    assert caplog.text.count("disabled") == 1
    with pytest.raises(ConfigError, match="secret"):
        resolve("os.environ/MISSING_TEST_SECRET", "file", "secret")
    monkeypatch.setenv("MISSING_TEST_SECRET", "fictional")
    assert resolve("os.environ/MISSING_TEST_SECRET", "file", "secret") == "fictional"
    assert resolve("literal", "file", "key") == "literal"


def test_file_errors_and_avatar(tmp_path):
    with pytest.raises(ConfigError):
        compile_registry(tmp_path / "absent")
    assert compile_registry(tmp_path).all() == []
    p = tmp_path / "agent.yaml"
    p.write_text("[")
    with pytest.raises(ConfigError, match="YAML"):
        load(p)
    p.unlink()
    with pytest.raises(ConfigError):
        load(p)
    src = Path("tests/fixtures/agents/plain-bot")
    shutil.copytree(src, tmp_path / "one")
    p = tmp_path / "one/agent.yaml"
    p.write_text(p.read_text().replace("avatar: 💬", "avatar: avatar.svg"))
    (p.parent / "avatar.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg"/>')
    assert load(p).avatar_file
    p.write_text(p.read_text().replace("avatar.svg", "avatar.txt"))
    (p.parent / "avatar.txt").write_text("not an image")
    with pytest.raises(ConfigError, match="only SVG"):
        load(p)


def test_duplicate_tool(tmp_path):
    p = tmp_path / "one"
    shutil.copytree("tests/fixtures/agents/search-bot", p)
    source = p / "agent.yaml"
    source.write_text(source.read_text().replace("runtime:", "runtime:") + "\n")
    import yaml

    value = yaml.safe_load(source.read_text())
    value["tools"].append(value["tools"][0])
    source.write_text(yaml.safe_dump(value))
    with pytest.raises(ConfigError, match="duplicate native"):
        compile_registry(tmp_path)


def test_settings(monkeypatch):
    settings = Settings(_env_file=None)
    assert settings.trace_include_content is False
    assert Settings(_env_file=None, app_mode="offline").is_demo("named")
    online = Settings(
        _env_file=None,
        azure_foundry_endpoint="https://fictional.example",
        azure_foundry_deployment="chat",
    )
    assert not online.is_demo()
    assert online.effective_search_provider == "duckduckgo"
