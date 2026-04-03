"""Tests for config loading and validation."""

from pathlib import Path

import pytest

from pseudo2py.config import (
    Config,
    ConfigError,
    LLMConfig,
    SearchConfig,
    init_config,
    load_config,
    validate_config,
)


def test_load_config_from_toml(tmp_path: Path):
    config_file = tmp_path / "config.toml"
    config_file.write_text("""\
[llm]
base_url = "http://localhost:8000/v1"
model = "llama-3-70b"
api_key = "test-key"

[search]
provider = "brave"
brave_api_key = "BSA123"

[output]
save_dir = "/tmp/out"
""")
    cfg = load_config(config_file)
    assert cfg.llm.base_url == "http://localhost:8000/v1"
    assert cfg.llm.model == "llama-3-70b"
    assert cfg.llm.api_key == "test-key"
    assert cfg.search.provider == "brave"
    assert cfg.search.brave_api_key == "BSA123"
    assert cfg.output.save_dir == "/tmp/out"


def test_load_config_missing_file(tmp_path: Path):
    cfg = load_config(tmp_path / "nonexistent.toml")
    assert cfg.llm.base_url == ""
    assert cfg.search.provider == "duckduckgo"


def test_env_vars_override_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    config_file = tmp_path / "config.toml"
    config_file.write_text("""\
[llm]
base_url = "http://file-url/v1"
model = "file-model"
""")
    monkeypatch.setenv("PSEUDO2PY_BASE_URL", "http://env-url/v1")
    monkeypatch.setenv("PSEUDO2PY_MODEL", "env-model")
    cfg = load_config(config_file)
    assert cfg.llm.base_url == "http://env-url/v1"
    assert cfg.llm.model == "env-model"


def test_cli_overrides_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("PSEUDO2PY_BASE_URL", "http://env-url/v1")
    cfg = load_config(
        tmp_path / "none.toml",
        base_url="http://cli-url/v1",
        model="cli-model",
    )
    assert cfg.llm.base_url == "http://cli-url/v1"
    assert cfg.llm.model == "cli-model"


def test_validate_missing_base_url():
    cfg = Config(llm=LLMConfig(base_url="", model="some-model"))
    with pytest.raises(ConfigError, match="base_url is required"):
        validate_config(cfg)


def test_validate_missing_model():
    cfg = Config(llm=LLMConfig(base_url="http://x/v1", model=""))
    with pytest.raises(ConfigError, match="model is required"):
        validate_config(cfg)


def test_validate_brave_without_key():
    cfg = Config(
        llm=LLMConfig(base_url="http://x/v1", model="m"),
        search=SearchConfig(provider="brave", brave_api_key=""),
    )
    with pytest.raises(ConfigError, match="brave_api_key"):
        validate_config(cfg)


def test_validate_unknown_provider():
    cfg = Config(
        llm=LLMConfig(base_url="http://x/v1", model="m"),
        search=SearchConfig(provider="google"),
    )
    with pytest.raises(ConfigError, match="Unknown search provider"):
        validate_config(cfg)


def test_validate_happy_path():
    cfg = Config(
        llm=LLMConfig(base_url="http://x/v1", model="m"),
        search=SearchConfig(provider="duckduckgo"),
    )
    validate_config(cfg)  # should not raise


def test_init_config(tmp_path: Path):
    target = tmp_path / "sub" / "config.toml"
    result = init_config(target)
    assert result == target
    assert target.exists()
    content = target.read_text()
    assert "[llm]" in content
    assert "[search]" in content
