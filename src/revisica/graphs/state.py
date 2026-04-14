"""State schemas for LangGraph workflows.

Each graph has a typed state dict that flows through all nodes.
LangGraph manages state persistence, checkpointing, and streaming.
"""

from __future__ import annotations

import operator
from typing import Annotated, Any, TypedDict

from ..ingestion.types import RevisicaDocument
from ..profiles.config import FocusRequest, ReviewConfig


class UnifiedState(TypedDict, total=False):
    """Top-level state for the unified review graph."""

    # Input
    source_path: str
    run_dir: str
    config: ReviewConfig

    # After ingestion
    document: RevisicaDocument | None

    # After lane execution — store full run dataclass objects
    writing_result: Any  # WritingReviewRun | None
    math_result: Any  # MathReviewRun | None

    # Output
    unified_review_run: Any  # UnifiedReviewRun | None

    # HITL
    focus_requests: list[FocusRequest]
    focus_results: list[dict[str, Any]]

    # Accumulator (reducer: appends across nodes)
    warnings: Annotated[list[str], operator.add]


class WritingState(TypedDict, total=False):
    """State for the writing review subgraph."""

    # Input
    source_path: str
    run_dir: str
    config: ReviewConfig

    # After bootstrap_and_extract
    content: str
    sections: list[Any]
    section_combos: list[Any]
    claims: list[Any]
    platforms: dict[str, Any]  # name -> PlatformStatus
    selected_specs: list[Any]  # list[ProviderModelSpec]
    detected_providers: list[str]
    mode: str  # "cross-check" or "single-provider"
    schema_path: str | None
    working_dir: str
    venue_profile: str
    judge_spec: Any  # ProviderModelSpec | None

    # After role execution
    artifacts: list[Any]  # list[WritingRoleArtifact]

    # After judge
    final_report: Any  # ReviewResult | None

    # Output
    writing_review_run: Any  # WritingReviewRun | None

    # HITL (future)
    user_feedback: dict[str, Any] | None

    # Accumulator (reducer: appends across nodes)
    warnings: Annotated[list[str], operator.add]


class MathState(TypedDict, total=False):
    """State for the math review subgraph."""

    source_path: str
    content: str
    run_dir: str
    config: ReviewConfig

    # After extraction
    functions: list[Any]
    claims: list[Any]
    blueprints: list[Any]
    _theorems: list[Any]
    _proofs: list[Any]

    # After deterministic checks
    issues: list[Any]

    # After LLM review
    llm_provider_results: list[Any]
    llm_self_check_results: list[Any]
    llm_adjudication_results: list[Any]

    # HITL (future)
    user_feedback: dict[str, Any] | None

    # Accumulator (reducer: appends across nodes)
    warnings: Annotated[list[str], operator.add]


class PolishState(TypedDict, total=False):
    """State for the lightweight polish subgraph."""

    source_path: str
    content: str
    run_dir: str
    config: ReviewConfig
    report: str
    warnings: Annotated[list[str], operator.add]
