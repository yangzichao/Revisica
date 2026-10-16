"""Reviewer spec resolution and run-directory setup for the writing lane."""

from __future__ import annotations

from pathlib import Path

from ..bootstrap import PlatformStatus
from ..core_types import ProviderModelSpec
from ..providers.availability import default_runnable_specs, split_runnable_specs
from ..run_dir_helpers import create_review_run_dir


def resolve_reviewer_specs(
    platforms: dict[str, PlatformStatus],
    reviewer_specs: list[ProviderModelSpec] | None,
) -> tuple[list[ProviderModelSpec], list[str]]:
    warnings: list[str] = []
    if reviewer_specs:
        selected, unavailable = split_runnable_specs(reviewer_specs, platforms)
        if unavailable:
            warnings.append(
                "Requested writing-review provider(s) not available: " + ", ".join(unavailable) + "."
            )
    else:
        selected = default_runnable_specs(platforms)
    if not selected:
        raise RuntimeError(
            "No supported provider detected in the current environment. "
            "Install codex and/or claude and run `revisica bootstrap`, or configure an "
            "Anthropic/OpenAI API key."
        )
    if len(selected) == 1:
        warnings.append(
            "Only one provider is active for writing review, so Revisica will run specialized roles "
            "and final judging on a single provider. Cross-check quality may be lower."
        )
    return selected, warnings


def make_output_dir(source: Path, output_dir: str | None) -> Path:
    if not output_dir:
        return create_review_run_dir(f"{source.stem}-writing")
    target = Path(output_dir).expanduser().resolve()
    target.mkdir(parents=True, exist_ok=True)
    return target
