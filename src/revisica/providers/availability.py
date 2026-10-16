"""Which reviewer providers can run now, under the active backend mode.

``bootstrap.detect_platforms()`` only looks for the ``codex`` and
``claude`` binaries. The review lanes used it as the whole truth, so in
API mode (keys, no CLIs) every review failed with "No supported provider
detected", and an explicit ``anthropic-api`` reviewer raised ``KeyError``.

Here a provider name runs under one of three spellings:

- a logical name (``claude``, ``codex``), kept as-is when it runs on the
  CLI so artifact names and model routes stay what they were;
- the API provider a logical name falls back to (``claude`` becomes
  ``anthropic-api`` in API mode, or in auto mode without the CLI), so
  model routing picks API model IDs instead of the CLI's ``sonnet``;
- a concrete name (``claude-cli``, ``anthropic-api``), run only if that
  exact backend is allowed and configured.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..core_types import ProviderModelSpec
from .provider_config import get_backend_mode

if TYPE_CHECKING:
    from ..bootstrap import PlatformStatus

DEFAULT_REVIEWER_PROVIDERS = ("codex", "claude")

_CLI_PROVIDER_FOR_NAME = {
    "codex": "codex",
    "claude": "claude",
    "codex-cli": "codex",
    "claude-cli": "claude",
}
_API_FALLBACK_FOR_LOGICAL_NAME = {
    "codex": "openai-api",
    "claude": "anthropic-api",
}
API_PROVIDER_NAMES = ("anthropic-api", "openai-api")
KNOWN_PROVIDER_NAMES = (*_CLI_PROVIDER_FOR_NAME, *API_PROVIDER_NAMES)


def runnable_provider_name(name: str, platforms: dict[str, "PlatformStatus"]) -> str | None:
    """The provider name to run ``name`` under, or None if it cannot run now."""
    mode = get_backend_mode()
    cli_platform_name = _CLI_PROVIDER_FOR_NAME.get(name)
    if cli_platform_name is not None:
        platform = platforms.get(cli_platform_name)
        if mode != "api" and platform is not None and platform.available:
            return name
        api_fallback = _API_FALLBACK_FOR_LOGICAL_NAME.get(name)
        if api_fallback is not None and mode != "cli" and _api_provider_configured(api_fallback):
            return api_fallback
        return None
    if name in API_PROVIDER_NAMES and mode != "cli" and _api_provider_configured(name):
        return name
    return None


def runnable_spec(spec: ProviderModelSpec, platforms: dict[str, "PlatformStatus"]) -> ProviderModelSpec | None:
    provider_name = runnable_provider_name(spec.provider, platforms)
    if provider_name is None:
        return None
    return ProviderModelSpec(provider=provider_name, model=spec.model)


def default_runnable_specs(platforms: dict[str, "PlatformStatus"]) -> list[ProviderModelSpec]:
    """One spec per default reviewer provider that can run now."""
    specs: list[ProviderModelSpec] = []
    for name in DEFAULT_REVIEWER_PROVIDERS:
        provider_name = runnable_provider_name(name, platforms)
        if provider_name is not None:
            specs.append(ProviderModelSpec(provider=provider_name))
    return specs


def split_runnable_specs(
    requested_specs: list[ProviderModelSpec],
    platforms: dict[str, "PlatformStatus"],
) -> tuple[list[ProviderModelSpec], list[str]]:
    """Requested specs that can run, and labels of the ones that cannot."""
    runnable: list[ProviderModelSpec] = []
    unavailable_labels: list[str] = []
    for spec in requested_specs:
        resolved = runnable_spec(spec, platforms)
        if resolved is None:
            unavailable_labels.append(_unavailable_label(spec))
        else:
            runnable.append(resolved)
    return runnable, unavailable_labels


def _unavailable_label(spec: ProviderModelSpec) -> str:
    if spec.provider not in KNOWN_PROVIDER_NAMES:
        return f"{spec.label} (unknown provider; use one of: {', '.join(KNOWN_PROVIDER_NAMES)})"
    return spec.label


def _api_provider_configured(provider_name: str) -> bool:
    from . import get_registry

    try:
        provider = get_registry().get(provider_name)
    except ValueError:
        return False
    return provider.is_available()
