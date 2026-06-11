"""Shared dataclasses and role constants for the writing review lane."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ..core_types import ProviderModelSpec, ReviewResult

WRITING_ROLES = ("basic", "structure", "venue")
MATH_VERIFICATION_ROLES = ("math-claim-verifier", "notation-tracker", "formula-cross-checker")

# Maximum parallel workers for role/section-combo tasks
MAX_PARALLEL_WORKERS = 12


@dataclass
class WritingRoleArtifact:
    role: str
    provider: str
    model: str | None
    result: ReviewResult
    findings: list[dict[str, object]] | None


@dataclass
class WritingReviewRun:
    source: Path
    run_dir: Path
    venue_profile: str
    detected_providers: list[str]
    reviewer_specs: list[ProviderModelSpec]
    judge_spec: ProviderModelSpec | None
    mode: str
    artifacts: list[WritingRoleArtifact]
    final_report: ReviewResult | None
    warnings: list[str]
