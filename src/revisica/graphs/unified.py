"""Unified review graph — top-level orchestrator.

Routes by mode:
- POLISH → polish subgraph
- REVIEW → ingest → writing lane → math lane → summary
"""

from __future__ import annotations

import functools
import logging
from datetime import datetime
import json
from pathlib import Path
from typing import Any

from langgraph.graph import END, StateGraph

from ..ingestion import parse_document
from ..math_review import MathReviewRun, review_math_file
from ..profiles.config import ReviewConfig, ReviewMode
from ..unified_review import UnifiedReviewRun
from .state import UnifiedState

logger = logging.getLogger(__name__)


# ── node functions ──────────────────────────────────────────────────


def route_by_mode(state: UnifiedState) -> str:
    """Route to the correct subgraph based on review mode."""
    config = state.get("config")
    if config and config.mode == ReviewMode.POLISH:
        return "run_polish"
    return "ingest_document"


def ingest_document(state: UnifiedState) -> dict:
    """Parse input file into a RevisicaDocument."""
    source_path = state["source_path"]
    parser_choice = state.get("parser", "auto") or "auto"
    mineru_backend = state.get("mineru_backend") or None
    try:
        document = parse_document(
            source_path,
            parser=parser_choice,
            mineru_backend=mineru_backend,
        )
        logger.info(
            "Ingested %s via %s: %s (%d sections)",
            Path(source_path).name,
            document.parser_used,
            document.metadata.title or "(no title)",
            len(document.sections),
        )
    except Exception as exc:
        logger.warning("Ingestion failed, falling back to raw read: %s", exc)
        document = None
    return {"document": document}


def run_writing_lane(state: UnifiedState) -> dict:
    """Run the writing review subgraph."""
    from .writing import compile_writing_graph

    source_path = state["source_path"]
    run_dir_base = state["run_dir"]
    config = state.get("config")

    writing_dir = str(Path(run_dir_base) / "writing")
    writing_config = ReviewConfig(
        mode=ReviewMode.REVIEW,
        venue_profile=config.venue_profile if config else "general-academic",
        providers=config.providers if config else [],
        judge_spec=config.judge_spec if config else None,
        force_bootstrap=config.force_bootstrap if config else False,
        timeout_seconds=config.timeout_seconds if config else 120,
    )

    warnings: list[str] = []
    try:
        graph = compile_writing_graph()
        final_state = graph.invoke({
            "source_path": source_path,
            "run_dir": writing_dir,
            "config": writing_config,
            "warnings": [],
        })
        writing_result = final_state.get("writing_review_run")
    except Exception as error:
        warnings.append(f"Writing review lane failed: {error}")
        writing_result = None

    return {
        "writing_result": writing_result,
        "warnings": warnings,
    }


def run_math_lane(state: UnifiedState) -> dict:
    """Run the math review pipeline.

    If the ingestion step produced a :class:`RevisicaDocument`, we reuse
    its normalized markdown so the extractors see the parsed text (e.g.
    Markdown derived from a PDF via MinerU/Mathpix) rather than the raw
    bytes on disk. This matters for non-.tex papers, where re-reading
    the source file would bypass the ingestion pipeline entirely.
    """
    source_path = state["source_path"]
    run_dir_base = state["run_dir"]
    config = state.get("config")
    document = state.get("document")

    math_dir = str(Path(run_dir_base) / "math")
    content_override = document.markdown if document is not None else None

    warnings: list[str] = []
    try:
        math_result = review_math_file(
            file_path=source_path,
            output_dir=math_dir,
            llm_proof_review=config.llm_proof_review if config else False,
            targets=config.math_targets if config else None,
            reviewer_specs=config.math_reviewer_specs if config else None,
            self_check_spec=config.self_check_spec if config else None,
            adjudicator_spec=config.adjudicator_spec if config else None,
            force_bootstrap=config.force_bootstrap if config else False,
            timeout_seconds=config.timeout_seconds if config else 120,
            agent_version=config.agent_version if config else None,
            content_override=content_override,
        )
    except Exception as error:
        warnings.append(f"Math review lane failed: {error}")
        math_result = None

    return {
        "math_result": math_result,
        "warnings": warnings,
    }


def run_polish(state: UnifiedState) -> dict:
    """Run polish mode (lightweight, writing only)."""
    from .polish import compile_polish_graph

    source_path = state["source_path"]
    run_dir = state["run_dir"]
    config = state.get("config")

    polish_warnings: list[str] = []
    try:
        polish_graph = compile_polish_graph()
        polish_result = polish_graph.invoke({
            "source_path": source_path,
            "run_dir": run_dir,
            "config": config,
            "warnings": [],
        })
        polish_warnings.extend(polish_result.get("warnings", []))
    except Exception as error:
        polish_warnings.append(f"Polish lane failed: {error}")

    run = UnifiedReviewRun(
        source=Path(source_path).expanduser().resolve(),
        run_dir=Path(run_dir),
        writing=None,
        math=None,
        warnings=list(polish_warnings),
    )
    return {
        "unified_review_run": run,
        "warnings": polish_warnings,
    }


def write_unified_summary(state: UnifiedState) -> dict:
    """Write unified summary and construct UnifiedReviewRun."""
    source_path = state["source_path"]
    run_dir = Path(state["run_dir"])
    run_dir.mkdir(parents=True, exist_ok=True)
    warnings = state.get("warnings", [])
    writing_result = state.get("writing_result")  # WritingReviewRun | None
    math_result = state.get("math_result")  # MathReviewRun | None

    _write_summary(run_dir, Path(source_path), writing_result, math_result, warnings)

    run = UnifiedReviewRun(
        source=Path(source_path).expanduser().resolve(),
        run_dir=run_dir,
        writing=writing_result,
        math=math_result,
        warnings=warnings,
    )
    return {"unified_review_run": run}


# ── summary writer ─────────────────────────────────────────────────


def _write_summary(
    run_dir: Path,
    source: Path,
    writing: Any,
    math: Any,
    warnings: list[str],
) -> None:
    lines = [
        "# Revisica Unified Review",
        "",
        f"- Source: `{source}`",
        f"- Timestamp: `{datetime.now().isoformat(timespec='seconds')}`",
        "",
        "## Lanes",
        "",
    ]

    if writing is not None:
        basic = sum(
            len(a.findings) for a in writing.artifacts
            if a.findings is not None and a.role == "basic"
        )
        structure = sum(
            len(a.findings) for a in writing.artifacts
            if a.findings is not None and a.role == "structure"
        )
        venue = sum(
            len(a.findings) for a in writing.artifacts
            if a.findings is not None and a.role == "venue"
        )
        lines.append(f"- Writing: completed (basic={basic}, structure={structure}, venue={venue})")
        lines.append(f"  - Venue profile: `{writing.venue_profile}`")
        lines.append(f"  - Mode: `{writing.mode}`")
        lines.append(f"  - Artifacts dir: `{writing.run_dir}`")
        if writing.final_report is not None:
            lines.append(f"  - Final report: `{writing.run_dir / 'final_report.md'}`")
    else:
        lines.append("- Writing: failed (see warnings)")

    lines.append("")

    if math is not None:
        refuted = sum(1 for i in math.issues if i.status == "machine-refuted")
        verified = sum(1 for i in math.issues if i.status == "machine-verified")
        suspected = sum(1 for i in math.issues if i.status == "llm-suspected")
        pending = sum(1 for i in math.issues if i.status == "needs-human-check")
        lines.append(
            f"- Math: completed (refuted={refuted}, verified={verified}, "
            f"suspected={suspected}, pending={pending}, blueprints={len(math.blueprints)})"
        )
        lines.append(f"  - Artifacts dir: `{math.run_dir}`")
        lines.append(f"  - Math report: `{math.run_dir / 'math_report.md'}`")
    else:
        lines.append("- Math: failed (see warnings)")

    if warnings:
        lines.extend(["", "## Warnings", ""])
        for warning in warnings:
            lines.append(f"- {warning}")

    (run_dir / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    metadata = {
        "source": str(source),
        "writing_dir": str(writing.run_dir) if writing else None,
        "math_dir": str(math.run_dir) if math else None,
        "warnings": warnings,
    }
    (run_dir / "summary.json").write_text(
        json.dumps(metadata, indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )


# ── graph construction ──────────────────────────────────────────────


def build_unified_graph() -> StateGraph:
    """Build the unified review graph."""
    builder = StateGraph(UnifiedState)

    builder.add_node("ingest_document", ingest_document)
    builder.add_node("run_writing_lane", run_writing_lane)
    builder.add_node("run_math_lane", run_math_lane)
    builder.add_node("write_unified_summary", write_unified_summary)
    builder.add_node("run_polish", run_polish)

    builder.set_conditional_entry_point(
        route_by_mode,
        {
            "run_polish": "run_polish",
            "ingest_document": "ingest_document",
        },
    )
    builder.add_edge("run_polish", END)
    builder.add_edge("ingest_document", "run_writing_lane")
    builder.add_edge("run_writing_lane", "run_math_lane")
    builder.add_edge("run_math_lane", "write_unified_summary")
    builder.add_edge("write_unified_summary", END)

    return builder


@functools.cache
def compile_unified_graph():
    """Compile the unified graph ready for execution (cached)."""
    return build_unified_graph().compile()
