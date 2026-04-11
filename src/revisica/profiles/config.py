"""Core configuration types for review modes."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from ..core_types import ProviderModelSpec


class ReviewMode(Enum):
    """Top-level review mode selection."""

    POLISH = "polish"
    REVIEW = "review"


@dataclass
class ReviewConfig:
    """Full configuration for a review run.

    Combines the mode selection with provider/venue/timeout settings.
    Polish mode ignores cross_check and math-related settings.
    """

    mode: ReviewMode = ReviewMode.REVIEW
    venue_profile: str = "general-academic"
    custom_instructions: str | None = None
    providers: list[ProviderModelSpec] = field(default_factory=list)
    judge_spec: ProviderModelSpec | None = None
    cross_check: bool = True
    llm_proof_review: bool = False
    timeout_seconds: int = 120
    force_bootstrap: bool = False


@dataclass
class FocusRequest:
    """A user request to deeply analyze a specific section.

    Triggered from HITL interaction (user clicks a section in the UI)
    or from CLI: ``revisica focus paper.pdf --section sec-3 --instruction "..."``.
    """

    section_id: str
    instruction: str
    depth: str = "deep"
