"""Math review subgraph.

Wraps existing math pipeline as LangGraph nodes:
extract → deterministic checks → (conditional) LLM review → write report.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from langgraph.graph import END, StateGraph

from ..math_artifacts import write_math_artifacts
from ..math_deterministic import analyze_blueprints, analyze_claims, issue_sort_key
from ..math_extraction import (
    build_proof_blueprints,
    extract_claims,
    extract_functions,
    extract_proof_blocks,
    extract_theorem_blocks,
)
from ..math_llm_review import run_llm_proof_review
from ..math_types import MathIssue
from .state import MathState


# ── node functions ──────────────────────────────────────────────────


def read_and_extract(state: MathState) -> dict:
    """Read paper and extract math structures."""
    source_path = state["source_path"]
    content = Path(source_path).read_text(encoding="utf-8")

    functions = extract_functions(content)
    claims = extract_claims(content, functions)
    theorems = extract_theorem_blocks(content)
    proofs = extract_proof_blocks(content)
    blueprints = build_proof_blueprints(theorems, proofs)

    return {
        "content": content,
        "functions": functions,
        "claims": claims,
        "blueprints": blueprints,
    }


def run_deterministic_checks(state: MathState) -> dict:
    """Run SymPy-based deterministic math checks."""
    functions = state.get("functions", [])
    claims = state.get("claims", [])
    blueprints = state.get("blueprints", [])
    content = state.get("content", "")

    issues: list[MathIssue] = []
    issues.extend(analyze_claims(claims, functions))

    # analyze_blueprints needs proof blocks
    proofs = extract_proof_blocks(content)
    issues.extend(analyze_blueprints(blueprints, proofs))

    return {"issues": issues}


def should_run_llm_review(state: MathState) -> str:
    """Conditional edge: run LLM review if configured."""
    config = state.get("config")
    if config and config.llm_proof_review:
        return "run_llm_review"
    return "write_math_report"


def run_llm_review(state: MathState) -> dict:
    """Run LLM-based proof review (optional, parallel per blueprint)."""
    source = Path(state["source_path"])
    blueprints = state.get("blueprints", [])
    config = state.get("config")

    if not config or not blueprints:
        return {}

    targets = None
    reviewer_specs = config.providers or None
    llm_issues, llm_provider_results, llm_self_check_results, llm_adjudication_results, llm_warnings = (
        run_llm_proof_review(
            source=source,
            blueprints=blueprints,
            targets=targets,
            proof_review_mode="auto",
            reviewer_specs=reviewer_specs,
            force_bootstrap=config.force_bootstrap,
            timeout_seconds=config.timeout_seconds,
        )
    )

    existing_issues = state.get("issues", [])
    combined_issues = list(existing_issues) + list(llm_issues)

    return {
        "issues": combined_issues,
        "llm_provider_results": llm_provider_results,
        "llm_self_check_results": llm_self_check_results,
        "llm_adjudication_results": llm_adjudication_results,
        "warnings": state.get("warnings", []) + llm_warnings,
    }


def write_math_report(state: MathState) -> dict:
    """Sort issues and write math artifacts to disk."""
    run_dir = Path(state["run_dir"])
    run_dir.mkdir(parents=True, exist_ok=True)
    source = Path(state["source_path"])
    content = state.get("content", "")

    functions = state.get("functions", [])
    claims = state.get("claims", [])
    blueprints = state.get("blueprints", [])
    issues = state.get("issues", [])
    llm_provider_results = state.get("llm_provider_results", [])
    llm_self_check_results = state.get("llm_self_check_results", [])
    llm_adjudication_results = state.get("llm_adjudication_results", [])
    warnings = state.get("warnings", [])

    issues.sort(key=issue_sort_key)

    theorems = extract_theorem_blocks(content)
    proofs = extract_proof_blocks(content)

    write_math_artifacts(
        run_dir, source,
        functions, claims, theorems, proofs, blueprints,
        issues,
        llm_provider_results, llm_self_check_results, llm_adjudication_results,
        warnings,
    )
    return {}


# ── graph construction ──────────────────────────────────────────────


def build_math_graph() -> StateGraph:
    """Build the math review subgraph."""
    builder = StateGraph(MathState)

    builder.add_node("read_and_extract", read_and_extract)
    builder.add_node("run_deterministic_checks", run_deterministic_checks)
    builder.add_node("run_llm_review", run_llm_review)
    builder.add_node("write_math_report", write_math_report)

    builder.set_entry_point("read_and_extract")
    builder.add_edge("read_and_extract", "run_deterministic_checks")
    builder.add_conditional_edges(
        "run_deterministic_checks",
        should_run_llm_review,
        {"run_llm_review": "run_llm_review", "write_math_report": "write_math_report"},
    )
    builder.add_edge("run_llm_review", "write_math_report")
    builder.add_edge("write_math_report", END)

    return builder


def compile_math_graph():
    """Compile the math graph ready for execution."""
    return build_math_graph().compile()
