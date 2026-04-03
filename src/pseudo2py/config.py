"""Configuration loading and validation.

Resolution order: CLI flags > env vars > config file > defaults.
"""

from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

DEFAULT_CONFIG_PATH = Path.home() / ".config" / "pseudo2py" / "config.toml"

DEFAULT_CONFIG = """\
[llm]
base_url = ""          # Required: OpenAI-compatible endpoint (e.g. http://localhost:8000/v1)
model = ""             # Required: model name (e.g. meta-llama/Llama-3-70B)
api_key = "not-needed" # Optional: some backends require it

[search]
provider = "duckduckgo" # "brave" or "duckduckgo"
brave_api_key = ""      # Required if provider = "brave"

[output]
save_dir = "."
"""


@dataclass
class LLMConfig:
    base_url: str
    model: str
    api_key: str = "not-needed"


@dataclass
class SearchConfig:
    provider: str = "duckduckgo"
    brave_api_key: str = ""


@dataclass
class OutputConfig:
    save_dir: str = "."


@dataclass
class Config:
    llm: LLMConfig = field(default_factory=lambda: LLMConfig(base_url="", model=""))
    search: SearchConfig = field(default_factory=SearchConfig)
    output: OutputConfig = field(default_factory=OutputConfig)


class ConfigError(Exception):
    """Raised when config is missing or invalid."""


def load_config(
    config_path: Path | None = None,
    *,
    base_url: str | None = None,
    model: str | None = None,
    api_key: str | None = None,
) -> Config:
    """Load config from TOML file, then overlay env vars, then CLI overrides."""
    path = config_path or DEFAULT_CONFIG_PATH
    raw: dict = {}

    if path.exists():
        raw = tomllib.loads(path.read_text())

    # Build config from file
    llm_raw = raw.get("llm", {})
    search_raw = raw.get("search", {})
    output_raw = raw.get("output", {})

    config = Config(
        llm=LLMConfig(
            base_url=llm_raw.get("base_url", ""),
            model=llm_raw.get("model", ""),
            api_key=llm_raw.get("api_key", "not-needed"),
        ),
        search=SearchConfig(
            provider=search_raw.get("provider", "duckduckgo"),
            brave_api_key=search_raw.get("brave_api_key", ""),
        ),
        output=OutputConfig(
            save_dir=output_raw.get("save_dir", "."),
        ),
    )

    # Env var overlay
    if env_url := os.environ.get("PSEUDO2PY_BASE_URL"):
        config.llm.base_url = env_url
    if env_model := os.environ.get("PSEUDO2PY_MODEL"):
        config.llm.model = env_model
    if env_key := os.environ.get("PSEUDO2PY_API_KEY"):
        config.llm.api_key = env_key
    if env_provider := os.environ.get("PSEUDO2PY_SEARCH_PROVIDER"):
        config.search.provider = env_provider
    if env_brave := os.environ.get("BRAVE_API_KEY"):
        config.search.brave_api_key = env_brave

    # CLI override
    if base_url:
        config.llm.base_url = base_url
    if model:
        config.llm.model = model
    if api_key:
        config.llm.api_key = api_key

    return config


def validate_config(config: Config) -> None:
    """Raise ConfigError if required fields are missing."""
    if not config.llm.base_url:
        raise ConfigError(
            "LLM base_url is required. Set it in config.toml, "
            "PSEUDO2PY_BASE_URL env var, or run 'pseudo2py init'."
        )
    if not config.llm.model:
        raise ConfigError(
            "LLM model is required. Set it in config.toml, "
            "PSEUDO2PY_MODEL env var, or run 'pseudo2py init'."
        )
    if config.search.provider == "brave" and not config.search.brave_api_key:
        raise ConfigError(
            "Brave Search requires brave_api_key. Set it in config.toml "
            "or BRAVE_API_KEY env var, or switch provider to 'duckduckgo'."
        )
    if config.search.provider not in ("brave", "duckduckgo"):
        raise ConfigError(
            f"Unknown search provider '{config.search.provider}'. "
            "Use 'brave' or 'duckduckgo'."
        )


def init_config(path: Path | None = None) -> Path:
    """Write default config file. Returns path written."""
    target = path or DEFAULT_CONFIG_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(DEFAULT_CONFIG)
    return target
