"""Unified review graph — top-level orchestrator.

Routes by mode:
- POLISH → polish subgraph
- REVIEW → parallel [writing | math] → merge → report
"""

from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path
from typing import Any

from langgraph.graph import END, StateGraph

from ..math_review import review_math_file
from ..profiles.config import ReviewMode
from ..writing_review import review_writing_file
from .state import UnifiedState


# ── node functions ──────────────────────────────────────────────────


def route_by_mode(state: UnifiedState) -> str:
    """Route to the correct subgraph based on review mode."""
    config = state.get("config")
    if config and config.mode == ReviewMode.POLISH:
        return "run_polish"
    return "run_full_review"


def run_polish(state: UnifiedState) -> dict:
    """Run polish mode (lightweight, writing only)."""
    from .polish import compile_polish_graph

    source_path = state["source_path"]
    run_dir = state["run_dir"]
    config = state.get("config")

    polish_graph = compile_polish_graph()
    polish_result = polish_graph.invoke({
        "source_path": source_path,
        "run_dir": run_dir,
        "config": config,
        "warnings": [],
    })

    return {
        "warnings": polish_result.get("warnings", []),
    }


def run_full_review(state: UnifiedState) -> dict:
    """Run full review mode: writing + math lanes concurrently.

    Currently uses the existing ThreadPoolExecutor pattern inside
    review_writing_file() and review_math_file().  The outer parallel
    execution (writing vs math) is handled here sequentially for now —
    LangGraph parallel branches will replace this in a future iteration.
    """
    source_path = state["source_path"]
    run_dir_base = state["run_dir"]
    config = state.get("config")

    writing_dir = str(Path(run_dir_base) / "writing")
    math_dir = str(Path(run_dir_base) / "math")

    reviewer_specs = config.providers if config else None
    judge_spec = config.judge_spec if config else None
    venue_profile = config.venue_profile if config else "general-academic"
    force_bootstrap = config.force_bootstrap if config else False
    timeout_seconds = config.timeout_seconds if config else 120
    llm_proof_review = config.llm_proof_review if config else False

    warnings: list[str] = []
    writing_result_dict: dict[str, Any] | None = None
    math_result_dict: dict[str, Any] | None = None

    # Writing lane
    try:
        writing_result = review_writing_file(
            file_path=source_path,
            output_dir=writing_dir,
            venue_profile=venue_profile,
            reviewer_specs=reviewer_specs,
            judge_spec=judge_spec,
            force_bootstrap=force_bootstrap,
            timeout_seconds=timeout_seconds,
        )
        writing_result_dict = {
            "run_dir": str(writing_result.run_dir),
            "mode": writing_result.mode,
            "artifact_count": len(writing_result.artifacts),
            "has_final_report": writing_result.final_report is not None,
        }
    except Exception as error:
        warnings.append(f"Writing review lane failed: {error}")

    # Math lane
    try:
        math_result = review_math_file(
            file_path=source_path,
            output_dir=math_dir,
            llm_proof_review=llm_proof_review,
            force_bootstrap=force_bootstrap,
            timeout_seconds=timeout_seconds,
        )
        math_result_dict = {
            "run_dir": str(math_result.run_dir),
            "issues_count": len(math_result.issues),
            "blueprints_count": len(math_result.blueprints),
        }
    except Exception as error:
        warnings.append(f"Math review lane failed: {error}")

    return {
        "writing_result": writing_result_dict,
        "math_result": math_result_dict,
        "warnings": warnings,
    }


def write_unified_summary(state: UnifiedState) -> dict:
    """Write the unified summary linking both lanes."""
    run_dir = Path(state["run_dir"])
    run_dir.mkdir(parents=True, exist_ok=True)
    source_path = state["source_path"]
    warnings = state.get("warnings", [])
    writing_result = state.get("writing_result")
    math_result = state.get("math_result")

    lines = [
        "# Revisica Unified Review",
        "",
        f"- Source: `{source_path}`",
        f"- Timestamp: `{datetime.now().isoformat(timespec='seconds')}`",
        "",
        "## Lanes",
        "",
    ]

    if writing_result:
        lines.append(f"- Writing: completed ({writing_result.get('artifact_count', 0)} role runs)")
        lines.append(f"  - Artifacts dir: `{writing_result.get('run_dir', '')}`")
    else:
        lines.append("- Writing: failed (see warnings)")

    lines.append("")

    if math_result:
        lines.append(
            f"- Math: completed (issues={math_result.get('issues_count', 0)}, "
            f"blueprints={math_result.get('blueprints_count', 0)})"
        )
        lines.append(f"  - Artifacts dir: `{math_result.get('run_dir', '')}`")
    else:
        lines.append("- Math: failed (see warnings)")

    if warnings:
        lines.extend(["", "## Warnings", ""])
        for warning in warnings:
            lines.append(f"- {warning}")

    (run_dir / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    metadata = {
        "source": source_path,
        "writing_dir": writing_result.get("run_dir") if writing_result else None,
        "math_dir": math_result.get("run_dir") if math_result else None,
        "warnings": warnings,
    }
    (run_dir / "summary.json").write_text(
        json.dumps(metadata, indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )

    return {}


# ── graph construction ──────────────────────────────────────────────


def build_unified_graph() -> StateGraph:
    """Build the unified review graph."""
    builder = StateGraph(UnifiedState)

    builder.add_node("run_polish", run_polish)
    builder.add_node("run_full_review", run_full_review)
    builder.add_node("write_unified_summary", write_unified_summary)

    builder.set_conditional_entry_point(
        route_by_mode,
        {"run_polish": "run_polish", "run_full_review": "run_full_review"},
    )
    builder.add_edge("run_polish", END)
    builder.add_edge("run_full_review", "write_unified_summary")
    builder.add_edge("write_unified_summary", END)

    return builder


def compile_unified_graph():
    """Compile the unified graph ready for execution."""
    return build_unified_graph().compile()
