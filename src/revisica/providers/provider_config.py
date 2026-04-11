"""Provider configuration: load/save ~/.revisica/config.json."""

from __future__ import annotations

import json
import os
from pathlib import Path

CONFIG_DIR = Path.home() / ".revisica"
CONFIG_PATH = CONFIG_DIR / "config.json"


def _default_config() -> dict:
    return {
        "providers": {
            "claude-cli": {"enabled": True},
            "codex-cli": {"enabled": True},
            "anthropic-api": {},
            "openai-api": {},
        }
    }


def load_config() -> dict:
    """Load provider config from disk, merging with env vars."""
    if CONFIG_PATH.exists():
        raw = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    else:
        raw = _default_config()

    providers = raw.get("providers", {})

    # Env vars override config file for API keys
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
    if anthropic_key:
        providers.setdefault("anthropic-api", {})["api_key"] = anthropic_key

    openai_key = os.environ.get("OPENAI_API_KEY")
    if openai_key:
        providers.setdefault("openai-api", {})["api_key"] = openai_key

    mathpix_key = os.environ.get("MATHPIX_API_KEY")
    if mathpix_key:
        providers.setdefault("mathpix", {})["api_key"] = mathpix_key

    raw["providers"] = providers
    return raw


def save_config(config: dict) -> None:
    """Save provider config to disk."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(
        json.dumps(config, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def get_provider_config(provider_name: str) -> dict:
    """Get config for a specific provider."""
    config = load_config()
    return config.get("providers", {}).get(provider_name, {})
