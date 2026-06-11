"""Public entry point for the writing review lane."""

from __future__ import annotations

from ..core_types import ProviderModelSpec
from .types import WritingReviewRun


def review_writing_file(
    file_path: str,
    output_dir: str | None = None,
    venue_profile: str = "general-academic",
    reviewer_specs: list[ProviderModelSpec] | None = None,
    judge_spec: ProviderModelSpec | None = None,
    force_bootstrap: bool = False,
    timeout_seconds: int = 120,
    codex_reasoning_effort: str | None = None,
) -> WritingReviewRun:
    """Run the writing review pipeline via LangGraph."""
    from ..graphs.writing import compile_writing_graph
    from ..profiles.config import ReviewConfig, ReviewMode

    config = ReviewConfig(
        mode=ReviewMode.REVIEW,
        venue_profile=venue_profile,
        providers=reviewer_specs or [],
        judge_spec=judge_spec,
        force_bootstrap=force_bootstrap,
        timeout_seconds=timeout_seconds,
        codex_reasoning_effort=codex_reasoning_effort,
    )

    graph = compile_writing_graph()
    final_state = graph.invoke({
        "source_path": file_path,
        "run_dir": output_dir or "",
        "config": config,
        "warnings": [],
    })

    return final_state["writing_review_run"]
