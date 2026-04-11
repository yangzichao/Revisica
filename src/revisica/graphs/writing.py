"""Writing review subgraph.

Currently wraps the existing writing_review.review_writing_file() as a
single node.  Future iterations will decompose it into individual nodes
for parallel role execution, self-check, and judge — enabling HITL
interrupt between self-check and judge.
"""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any

from langgraph.graph import END, StateGraph

from ..writing_review import WritingReviewRun, review_writing_file
from .state import WritingState


# ── node functions ──────────────────────────────────────────────────


def run_writing_review(state: WritingState) -> dict:
    """Run the full writing review pipeline.

    This wraps the existing review_writing_file() function as a single
    node.  The internal parallelism (ThreadPoolExecutor with 12 workers)
    is preserved — LangGraph manages the outer orchestration while the
    inner parallelism stays as-is for now.
    """
    config = state.get("config")
    source_path = state["source_path"]
    run_dir = state["run_dir"]

    reviewer_specs = config.providers if config else None
    judge_spec = config.judge_spec if config else None
    venue_profile = config.venue_profile if config else "general-academic"
    force_bootstrap = config.force_bootstrap if config else False
    timeout_seconds = config.timeout_seconds if config else 120

    try:
        result = review_writing_file(
            file_path=source_path,
            output_dir=run_dir,
            venue_profile=venue_profile,
            reviewer_specs=reviewer_specs,
            judge_spec=judge_spec,
            force_bootstrap=force_bootstrap,
            timeout_seconds=timeout_seconds,
        )
        return {
            "artifacts": [_artifact_to_dict(a) for a in result.artifacts],
            "final_report": _report_to_dict(result.final_report) if result.final_report else None,
            "warnings": result.warnings,
        }
    except Exception as error:
        return {
            "warnings": [f"Writing review failed: {error}"],
        }


# ── helpers ─────────────────────────────────────────────────────────


def _artifact_to_dict(artifact) -> dict[str, Any]:
    """Convert WritingRoleArtifact to serializable dict."""
    return {
        "role": artifact.role,
        "provider": artifact.provider,
        "model": artifact.model,
        "success": artifact.result.success,
        "findings": artifact.findings,
    }


def _report_to_dict(report) -> dict[str, Any]:
    """Convert ReviewResult to serializable dict."""
    return {
        "provider": report.provider,
        "model": report.model,
        "success": report.success,
        "output": report.output,
    }


# ── graph construction ──────────────────────────────────────────────


def build_writing_graph() -> StateGraph:
    """Build the writing review subgraph."""
    builder = StateGraph(WritingState)

    builder.add_node("run_writing_review", run_writing_review)

    builder.set_entry_point("run_writing_review")
    builder.add_edge("run_writing_review", END)

    return builder


def compile_writing_graph():
    """Compile the writing graph ready for execution."""
    return build_writing_graph().compile()
