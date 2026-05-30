"""Configuration management for Radar Agent."""

import os
from pathlib import Path
from typing import Any

import yaml

DEFAULT_CONFIG_DIR = Path.home() / ".radar"
DEFAULT_CONFIG_FILE = DEFAULT_CONFIG_DIR / "config.yaml"

DEFAULT_CONFIG = {
    "llm": {
        "provider": "anthropic",
        "model": "claude-sonnet-4-20250514",
        "api_key": None,  # Falls back to ANTHROPIC_API_KEY env var
    },
    "watch": {
        "github_repos": [],
        "github_orgs": [],
        "github_topics": [],
        "hackernews_keywords": [],
        "producthunt_categories": [],
        "rss_feeds": [],
        "web_pages": [],
    },
    "digest": {
        "output_dir": str(DEFAULT_CONFIG_DIR / "digests"),
        "format": "markdown",  # markdown | json | both
        "language": "zh",  # zh | en
    },
    "schedule": {
        "enabled": False,
        "time": "09:00",
        "timezone": "Asia/Shanghai",
    },
}


class Config:
    """Manages radar configuration."""

    def __init__(self, config_path: str | None = None):
        self.path = Path(config_path) if config_path else DEFAULT_CONFIG_FILE
        self._data: dict[str, Any] = {}
        self.load()

    def load(self) -> None:
        """Load config from file, falling back to defaults."""
        if self.path.exists():
            with open(self.path) as f:
                user_config = yaml.safe_load(f) or {}
            self._data = self._deep_merge(DEFAULT_CONFIG, user_config)
        else:
            self._data = DEFAULT_CONFIG.copy()
            self._data["llm"]["api_key"] = os.environ.get("ANTHROPIC_API_KEY", "")

    def save(self) -> None:
        """Save current config to file."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, "w") as f:
            yaml.dump(self._data, f, default_flow_style=False, allow_unicode=True)

    def get(self, key: str, default: Any = None) -> Any:
        """Get a config value using dot notation."""
        keys = key.split(".")
        value = self._data
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
            if value is None:
                return default
        return value

    def set(self, key: str, value: Any) -> None:
        """Set a config value using dot notation."""
        keys = key.split(".")
        data = self._data
        for k in keys[:-1]:
            data = data.setdefault(k, {})
        data[keys[-1]] = value

    @property
    def api_key(self) -> str:
        """Get the LLM API key."""
        key = self.get("llm.api_key") or os.environ.get("ANTHROPIC_API_KEY", "")
        if not key:
            raise ValueError(
                "No API key found. Set ANTHROPIC_API_KEY env var or configure in ~/.radar/config.yaml"
            )
        return key

    @property
    def output_dir(self) -> Path:
        """Get the output directory for digests."""
        path = Path(self.get("digest.output_dir", str(DEFAULT_CONFIG_DIR / "digests")))
        path.mkdir(parents=True, exist_ok=True)
        return path

    @staticmethod
    def _deep_merge(base: dict, override: dict) -> dict:
        """Deep merge two dicts, override wins."""
        result = base.copy()
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = Config._deep_merge(result[key], value)
            else:
                result[key] = value
        return result

    @classmethod
    def init_config(cls, config_path: str | None = None) -> "Config":
        """Initialize a new config file with defaults."""
        config = cls.__new__(cls)
        config.path = Path(config_path) if config_path else DEFAULT_CONFIG_FILE
        config._data = DEFAULT_CONFIG.copy()
        config._data["llm"]["api_key"] = os.environ.get("ANTHROPIC_API_KEY", "")
        config.save()
        return config
