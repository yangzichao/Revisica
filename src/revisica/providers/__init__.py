"""Pluggable provider system for LLM access."""

from __future__ import annotations

from .base import BaseProvider
from .cli_claude import ClaudeCliProvider
from .cli_codex import CodexCliProvider

# ── backwards-compatible aliases ────────────────────────────────────

_ALIASES: dict[str, str] = {
    "codex": "codex-cli",
    "claude": "claude-cli",
}


class ProviderRegistry:
    """Discovers and manages available LLM providers."""

    def __init__(self) -> None:
        self._providers: dict[str, BaseProvider] = {}
        self._register_builtin_providers()

    def _register_builtin_providers(self) -> None:
        """Register all known providers (they report their own availability)."""
        self.register(CodexCliProvider())
        self.register(ClaudeCliProvider())

        # API providers — register if SDK is importable
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

    def get(self, name: str) -> BaseProvider:
        """Look up a provider by name (supports aliases like 'codex' → 'codex-cli')."""
        resolved_name = _ALIASES.get(name, name)
        provider = self._providers.get(resolved_name)
        if provider is None:
            available_names = list(self._providers.keys())
            raise ValueError(
                f"Unknown provider '{name}'. "
                f"Available: {available_names}"
            )
        return provider

    def list_all(self) -> list[BaseProvider]:
        """Return all registered providers."""
        return list(self._providers.values())

    def list_available(self) -> list[BaseProvider]:
        """Return only providers that are currently usable."""
        return [
            provider for provider in self._providers.values()
            if provider.is_available()
        ]


# Module-level singleton
_registry: ProviderRegistry | None = None


def get_registry() -> ProviderRegistry:
    """Get the global provider registry (lazy singleton)."""
    global _registry
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
