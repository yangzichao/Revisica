"""Default presets for Polish and Review modes."""

from __future__ import annotations

from .config import ReviewConfig, ReviewMode


POLISH_PRESET = ReviewConfig(
    mode=ReviewMode.POLISH,
    cross_check=False,
    llm_proof_review=False,
    timeout_seconds=90,
)

REVIEW_PRESET = ReviewConfig(
    mode=ReviewMode.REVIEW,
    cross_check=True,
    llm_proof_review=True,
    timeout_seconds=120,
)


def preset_for_mode(mode: ReviewMode) -> ReviewConfig:
    """Return the default preset for a given mode."""
    if mode is ReviewMode.POLISH:
        return ReviewConfig(
            mode=ReviewMode.POLISH,
            cross_check=False,
            llm_proof_review=False,
            timeout_seconds=90,
        )
    return ReviewConfig(
        mode=ReviewMode.REVIEW,
        cross_check=True,
        llm_proof_review=True,
        timeout_seconds=120,
    )
