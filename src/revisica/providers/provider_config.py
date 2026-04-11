"""Provider configuration: load/save ~/.revisica/config.json.

Central config for provider selection and backend mode.

``backend_mode`` controls which provider backends are active:

* ``"cli"``  — DMG distribution.  Uses ``claude`` / ``codex`` CLI tools
  (subscription-based, no API key needed).
* ``"api"``  — App Store / web distribution.  Uses Anthropic / OpenAI
  HTTP APIs (requires API keys).
* ``"auto"`` (default) — Prefer CLI if available, fall back to API.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Literal

BackendMode = Literal["cli", "api", "auto"]

CONFIG_DIR = Path.home() / ".revisica"
CONFIG_PATH = CONFIG_DIR / "config.json"


def _default_config() -> dict:
    return {
        "backend_mode": "auto",
        "providers": {
            "claude-cli": {"enabled": True},
            "codex-cli": {"enabled": True},
            "anthropic-api": {},
            "openai-api": {},
        },
    }


def load_config() -> dict:
    """Load provider config from disk, merging with env vars."""
    if CONFIG_PATH.exists():
        raw = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    else:
        raw = _default_config()

    # Ensure backend_mode always present
    raw.setdefault("backend_mode", "auto")

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

    # Env var override for backend mode
    env_mode = os.environ.get("REVISICA_BACKEND_MODE")
    if env_mode in ("cli", "api", "auto"):
        raw["backend_mode"] = env_mode

    raw["providers"] = providers
    return raw


def get_backend_mode() -> BackendMode:
    """Return the active backend mode."""
    mode = load_config().get("backend_mode", "auto")
    if mode not in ("cli", "api", "auto"):
        return "auto"
    return mode  # type: ignore[return-value]


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
