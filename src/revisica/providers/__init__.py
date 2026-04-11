"""Pluggable provider system for LLM access.

Providers are selected by *backend mode* (see ``provider_config.py``):

* ``cli``  — Only CLI providers (subscription-based).
* ``api``  — Only API providers (key-based).
* ``auto`` — Prefer CLI when available, fall back to API.

Logical names (``"claude"``, ``"codex"``) are resolved to a concrete
provider based on the active mode, so upper-layer code never needs to
know whether it's talking to a CLI or an HTTP API.
"""

from __future__ import annotations

import threading

from .base import BaseProvider
from .cli_claude import ClaudeCliProvider
from .cli_codex import CodexCliProvider
from .provider_config import BackendMode, get_backend_mode, get_provider_config

# ── alias tables per mode ─────────────────────────────────────────────
# Logical name → concrete provider name.

_CLI_ALIASES: dict[str, str] = {
    "codex": "codex-cli",
    "claude": "claude-cli",
}

_API_ALIASES: dict[str, str] = {
    "codex": "openai-api",
    "claude": "anthropic-api",
}


def _aliases_for_mode(mode: BackendMode) -> dict[str, str]:
    if mode == "cli":
        return _CLI_ALIASES
    if mode == "api":
        return _API_ALIASES
    # auto — filled dynamically at resolve time
    return {}


# ── registry ──────────────────────────────────────────────────────────

class ProviderRegistry:
    """Discovers and manages available LLM providers."""

    def __init__(self, mode: BackendMode | None = None) -> None:
        self._mode: BackendMode = mode or get_backend_mode()
        self._providers: dict[str, BaseProvider] = {}
        self._register_providers()

    @property
    def mode(self) -> BackendMode:
        return self._mode

    # ── registration ──────────────────────────────────────────────

    def _register_providers(self) -> None:
        """Register providers appropriate for the current mode."""
        if self._mode in ("cli", "auto"):
            self.register(CodexCliProvider())
            self.register(ClaudeCliProvider())

        if self._mode in ("api", "auto"):
            self._try_register_api_providers()

    def _try_register_api_providers(self) -> None:
        try:
            from .api_anthropic import AnthropicApiProvider
            self.register(AnthropicApiProvider())
        except ImportError:
            pass
        try:
            from .api_openai import OpenAiApiProvider
            self.register(OpenAiApiProvider())
        except ImportError:
            pass

    def register(self, provider: BaseProvider) -> None:
        """Register a provider instance."""
        self._providers[provider.name] = provider

    # ── lookup ────────────────────────────────────────────────────

    def _resolve_alias(self, name: str) -> str:
        """Resolve a logical name to a concrete provider name."""
        # Exact match — no aliasing needed.
        if name in self._providers:
            return name

        # Explicit mode aliases.
        aliases = _aliases_for_mode(self._mode)
        if name in aliases:
            return aliases[name]

        # Auto mode: prefer CLI if available, else API.
        if self._mode == "auto":
            cli_name = _CLI_ALIASES.get(name)
            api_name = _API_ALIASES.get(name)
            if cli_name and cli_name in self._providers:
                cli_provider = self._providers[cli_name]
                if cli_provider.is_available():
                    return cli_name
            if api_name and api_name in self._providers:
                return api_name
            # Fall through to CLI even if not available — let the error
            # message come from the provider itself.
            if cli_name:
                return cli_name

        return name

    def get(self, name: str) -> BaseProvider:
        """Look up a provider by name (supports logical aliases)."""
        resolved = self._resolve_alias(name)
        provider = self._providers.get(resolved)
        if provider is None:
            available_names = list(self._providers.keys())
            raise ValueError(
                f"Unknown provider '{name}' (resolved to '{resolved}'). "
                f"Available: {available_names}. Mode: {self._mode}"
            )
        return provider

    def list_all(self) -> list[BaseProvider]:
        return list(self._providers.values())

    def list_available(self) -> list[BaseProvider]:
        return [p for p in self._providers.values() if p.is_available()]


# ── module-level singleton ────────────────────────────────────────────

_registry: ProviderRegistry | None = None
_registry_lock = threading.Lock()


def get_registry() -> ProviderRegistry:
    """Get the global provider registry (lazy, thread-safe singleton)."""
    global _registry
    if _registry is None:
        with _registry_lock:
            if _registry is None:
                _registry = ProviderRegistry()
    return _registry


def get_provider(name: str) -> BaseProvider:
    """Shorthand for ``get_registry().get(name)``."""
    return get_registry().get(name)


__all__ = [
    "BaseProvider",
    "ClaudeCliProvider",
    "CodexCliProvider",
    "ProviderRegistry",
    "get_provider",
    "get_registry",
]
