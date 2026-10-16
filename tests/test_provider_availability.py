"""Review lanes must run on API providers, not only on the two CLIs.

Before: ``detect_platforms()`` (CLI binaries only) decided availability,
so ``REVISICA_BACKEND_MODE=api`` with a key failed with "No supported
provider detected", ``--reviewer-a anthropic-api:...`` raised
``KeyError: 'anthropic-api'``, and the provider registry kept the backend
mode the process started with after the app switched it.
"""

from __future__ import annotations

from pathlib import Path

import pytest

import revisica.graphs.polish as polish_graph_module
import revisica.providers as providers_package
from revisica.bootstrap import PlatformStatus
from revisica.core_types import ProviderModelSpec, ReviewResult
from revisica.math_llm.review import _resolve_math_reviewer_specs
from revisica.model_router import resolve_model_for_role
from revisica.profiles.config import ReviewConfig, ReviewMode
from revisica.providers import provider_config
from revisica.providers.availability import default_runnable_specs, runnable_provider_name
from revisica.writing.reviewer_resolution import resolve_reviewer_specs


def make_platforms(tmp_path: Path, claude_installed: bool, codex_installed: bool) -> dict[str, PlatformStatus]:
    return {
        "codex": PlatformStatus("codex", "/bin/codex" if codex_installed else None, tmp_path, tmp_path / "a"),
        "claude": PlatformStatus("claude", "/bin/claude" if claude_installed else None, tmp_path, tmp_path / "b"),
    }


@pytest.fixture
def isolated_config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """No config file, no API keys, auto mode — tests opt in to the rest."""
    monkeypatch.setattr(provider_config, "CONFIG_PATH", tmp_path / "missing-config.json")
    for variable in ("ANTHROPIC_API_KEY", "OPENAI_API_KEY", "REVISICA_BACKEND_MODE"):
        monkeypatch.delenv(variable, raising=False)
    return monkeypatch


def test_api_mode_reviews_with_api_keys_and_no_clis(tmp_path: Path, isolated_config) -> None:
    isolated_config.setenv("REVISICA_BACKEND_MODE", "api")
    isolated_config.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
    platforms = make_platforms(tmp_path, claude_installed=False, codex_installed=False)

    selected, _ = resolve_reviewer_specs(platforms, None)

    assert selected == [ProviderModelSpec("anthropic-api")]


def test_api_mode_ignores_installed_clis(tmp_path: Path, isolated_config) -> None:
    isolated_config.setenv("REVISICA_BACKEND_MODE", "api")
    isolated_config.setenv("OPENAI_API_KEY", "sk-test")
    platforms = make_platforms(tmp_path, claude_installed=True, codex_installed=True)

    assert default_runnable_specs(platforms) == [ProviderModelSpec("openai-api")]


def test_explicit_api_reviewer_does_not_raise(tmp_path: Path, isolated_config) -> None:
    isolated_config.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
    platforms = make_platforms(tmp_path, claude_installed=True, codex_installed=False)

    selected, warnings = resolve_reviewer_specs(platforms, [ProviderModelSpec("anthropic-api", "claude-sonnet-5-5")])

    assert selected == [ProviderModelSpec("anthropic-api", "claude-sonnet-5-5")]
    assert not any("not available" in warning for warning in warnings)


def test_cli_mode_refuses_api_reviewers(tmp_path: Path, isolated_config) -> None:
    isolated_config.setenv("REVISICA_BACKEND_MODE", "cli")
    isolated_config.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
    platforms = make_platforms(tmp_path, claude_installed=False, codex_installed=False)

    assert runnable_provider_name("anthropic-api", platforms) is None
    assert runnable_provider_name("claude", platforms) is None


def test_unknown_provider_name_is_reported_not_raised(tmp_path: Path, isolated_config) -> None:
    platforms = make_platforms(tmp_path, claude_installed=True, codex_installed=False)

    selected, warnings = resolve_reviewer_specs(
        platforms, [ProviderModelSpec("cluade"), ProviderModelSpec("claude", "sonnet")],
    )

    assert selected == [ProviderModelSpec("claude", "sonnet")]
    assert "cluade (unknown provider; use one of:" in warnings[0]


def test_auto_mode_keeps_the_cli_spelling_when_the_cli_is_installed(tmp_path: Path, isolated_config) -> None:
    isolated_config.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
    platforms = make_platforms(tmp_path, claude_installed=True, codex_installed=False)

    assert runnable_provider_name("claude", platforms) == "claude"


def test_auto_mode_falls_back_to_api_with_api_model_ids(tmp_path: Path, isolated_config) -> None:
    isolated_config.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
    platforms = make_platforms(tmp_path, claude_installed=False, codex_installed=False)

    selected, _ = resolve_reviewer_specs(platforms, [ProviderModelSpec("claude")])

    # The API rejects the CLI's "sonnet" alias; the route must be a model ID.
    assert resolve_model_for_role(selected[0], "basic") == ProviderModelSpec("anthropic-api", "claude-sonnet-5-5")


def test_math_lane_accepts_api_targets(tmp_path: Path, isolated_config) -> None:
    isolated_config.setenv("OPENAI_API_KEY", "sk-test")
    platforms = make_platforms(tmp_path, claude_installed=False, codex_installed=False)

    selected, warnings = _resolve_math_reviewer_specs(platforms, ["openai-api", "claude"], None)

    assert selected == [ProviderModelSpec("openai-api")]
    assert warnings == ["Requested math-review provider(s) not available: claude."]


def test_polish_runs_on_the_api_provider(tmp_path: Path, isolated_config) -> None:
    isolated_config.setenv("REVISICA_BACKEND_MODE", "api")
    isolated_config.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
    platforms = make_platforms(tmp_path, claude_installed=False, codex_installed=False)
    isolated_config.setattr(polish_graph_module, "detect_platforms", lambda: platforms)
    called_providers: list[str] = []

    def fake_run_provider_agent(provider_name, **kwargs):
        called_providers.append(provider_name)
        return ReviewResult(provider_name, kwargs.get("model"), [], 0, "Polished.", "")

    isolated_config.setattr(polish_graph_module, "run_provider_agent", fake_run_provider_agent)
    paper = tmp_path / "paper.md"
    paper.write_text("Draft.", encoding="utf-8")

    update = polish_graph_module.run_polish_agent(
        {"config": ReviewConfig(mode=ReviewMode.POLISH), "source_path": str(paper)},
    )

    assert called_providers == ["anthropic-api"]
    assert update["report"] == "Polished."


def test_registry_follows_backend_mode_changes(isolated_config) -> None:
    isolated_config.setenv("REVISICA_BACKEND_MODE", "cli")
    assert providers_package.get_registry().mode == "cli"

    isolated_config.setenv("REVISICA_BACKEND_MODE", "api")
    registry = providers_package.get_registry()

    assert registry.mode == "api"
    assert registry.get("claude").name == "anthropic-api"
