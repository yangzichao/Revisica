"""Reviewer spec resolution and run-directory setup for the writing lane."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from ..bootstrap import PlatformStatus
from ..core_types import ProviderModelSpec
from ..providers.availability import default_runnable_specs, split_runnable_specs


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
    if output_dir:
        target = Path(output_dir).expanduser().resolve()
    else:
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
        target = Path.cwd() / "reviews" / f"{source.stem}-writing-{stamp}"
    target.mkdir(parents=True, exist_ok=True)
    return target
