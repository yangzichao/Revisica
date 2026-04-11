"""State schemas for LangGraph workflows.

Each graph has a typed state dict that flows through all nodes.
LangGraph manages state persistence, checkpointing, and streaming.
"""

from __future__ import annotations

from typing import Any, TypedDict

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

    # After lane execution
    writing_result: dict[str, Any] | None
    math_result: dict[str, Any] | None

    # HITL
    focus_requests: list[FocusRequest]
    focus_results: list[dict[str, Any]]

    # Accumulator
    warnings: list[str]


class WritingState(TypedDict, total=False):
    """State for the writing review subgraph."""

    source_path: str
    content: str
    run_dir: str
    config: ReviewConfig

    # After section extraction
    sections: list[dict[str, Any]]
    section_combos: list[dict[str, Any]]
    claims: list[dict[str, Any]]

    # After role execution
    artifacts: list[dict[str, Any]]

    # After self-check
    self_check_results: list[dict[str, Any]]

    # HITL
    user_feedback: dict[str, Any] | None

    # After judge
    final_report: dict[str, Any] | None

    warnings: list[str]


class MathState(TypedDict, total=False):
    """State for the math review subgraph."""

    source_path: str
    content: str
    run_dir: str
    config: ReviewConfig

    # After extraction
    functions: list[dict[str, Any]]
    claims: list[dict[str, Any]]
    blueprints: list[dict[str, Any]]

    # After deterministic checks
    issues: list[dict[str, Any]]

    # After LLM review
    llm_provider_results: list[dict[str, Any]]
    llm_self_check_results: list[dict[str, Any]]
    llm_adjudication_results: list[dict[str, Any]]

    # HITL
    user_feedback: dict[str, Any] | None

    warnings: list[str]


class PolishState(TypedDict, total=False):
    """State for the lightweight polish subgraph."""

    source_path: str
    content: str
    run_dir: str
    config: ReviewConfig
    report: str
    warnings: list[str]
