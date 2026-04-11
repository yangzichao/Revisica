"""Focus subgraph — section-level deep dive.

Triggered from HITL interrupt or CLI: user selects a specific section
and provides instructions for targeted analysis.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, TypedDict

from langgraph.graph import END, StateGraph

from ..agents.registry import get_agent
from ..bootstrap import detect_platforms
from ..core_types import AgentSpec, ProviderModelSpec
from ..model_router import resolve_model_for_role
from ..profiles.config import FocusRequest
from ..review import _run_provider_agent


class FocusState(TypedDict, total=False):
    """State for the focus subgraph."""

    source_path: str
    run_dir: str
    focus_request: dict[str, Any]  # serialized FocusRequest
    providers: list[dict[str, Any]]
    timeout_seconds: int

    # After analysis
    writing_findings: str
    math_findings: str
    combined_report: str
    warnings: list[str]


# ── node functions ──────────────────────────────────────────────────


def run_focused_writing_review(state: FocusState) -> dict:
    """Run focused writing analysis on the specified section."""
    source_path = state["source_path"]
    focus_request = state.get("focus_request", {})
    section_id = focus_request.get("section_id", "")
    instruction = focus_request.get("instruction", "")
    timeout_seconds = state.get("timeout_seconds", 120)

    agent_definition = get_agent("writing-basic-reviewer")
    agent_spec = AgentSpec(
        name="focused-writing-reviewer",
        claude_agent_def={
            "instructions": agent_definition.system_prompt,
            "tools": agent_definition.tools,
        },
        codex_sandbox="read-only",
    )

    task_prompt = (
        f"Focus on section '{section_id}' in the draft at `{source_path}`.\n"
        f"Read the file, find this section, and deeply analyze it.\n"
        f"User instruction: {instruction}\n\n"
        f"Be thorough — this is a targeted deep dive, not a quick scan."
    )

    platforms = detect_platforms()
    provider_dicts = state.get("providers", [])
    if provider_dicts:
        first_provider = provider_dicts[0]
        provider_name = first_provider.get("provider", "claude")
    else:
        available = [name for name, p in platforms.items() if p.available]
        provider_name = available[0] if available else "claude"

    platform = platforms.get(provider_name)
    if not platform or not platform.available:
        return {"writing_findings": "", "warnings": [f"Provider '{provider_name}' not available for focus."]}

    spec = ProviderModelSpec(provider=provider_name)
    routed_spec = resolve_model_for_role(spec, "basic")

    result = _run_provider_agent(
        provider_name=routed_spec.provider,
        platform=platform,
        task_prompt=task_prompt,
        agent_spec=agent_spec,
        timeout_seconds=timeout_seconds,
        model=routed_spec.model,
        working_dir=str(Path(source_path).parent),
    )

    return {"writing_findings": result.output if result.success else ""}


def run_focused_math_review(state: FocusState) -> dict:
    """Run focused math analysis on the specified section."""
    source_path = state["source_path"]
    focus_request = state.get("focus_request", {})
    section_id = focus_request.get("section_id", "")
    instruction = focus_request.get("instruction", "")
    timeout_seconds = state.get("timeout_seconds", 120)

    agent_definition = get_agent("math-proof-reviewer")
    agent_spec = AgentSpec(
        name="focused-math-reviewer",
        claude_agent_def={
            "instructions": agent_definition.system_prompt,
            "tools": agent_definition.tools,
        },
        codex_sandbox="read-only",
    )

    task_prompt = (
        f"Focus on section '{section_id}' in the draft at `{source_path}`.\n"
        f"Read the file, find this section, and deeply analyze any math/proofs in it.\n"
        f"User instruction: {instruction}\n\n"
        f"Be thorough — check proof steps, verify claims, look for gaps."
    )

    platforms = detect_platforms()
    provider_dicts = state.get("providers", [])
    if provider_dicts:
        first_provider = provider_dicts[0]
        provider_name = first_provider.get("provider", "claude")
    else:
        available = [name for name, p in platforms.items() if p.available]
        provider_name = available[0] if available else "claude"

    platform = platforms.get(provider_name)
    if not platform or not platform.available:
        return {"math_findings": "", "warnings": [f"Provider '{provider_name}' not available for focus."]}

    spec = ProviderModelSpec(provider=provider_name)
    routed_spec = resolve_model_for_role(spec, "proof-reviewer")

    result = _run_provider_agent(
        provider_name=routed_spec.provider,
        platform=platform,
        task_prompt=task_prompt,
        agent_spec=agent_spec,
        timeout_seconds=timeout_seconds,
        model=routed_spec.model,
        working_dir=str(Path(source_path).parent),
    )

    return {"math_findings": result.output if result.success else ""}


def merge_focused_findings(state: FocusState) -> dict:
    """Merge writing and math focus findings into a combined report."""
    focus_request = state.get("focus_request", {})
    section_id = focus_request.get("section_id", "")
    instruction = focus_request.get("instruction", "")
    writing_findings = state.get("writing_findings", "")
    math_findings = state.get("math_findings", "")

    report_lines = [
        f"## Focus Analysis: {section_id}",
        "",
        f"**Instruction:** {instruction}",
        f"**Timestamp:** {datetime.now().isoformat(timespec='seconds')}",
        "",
    ]

    if writing_findings:
        report_lines.extend(["### Writing Analysis", "", writing_findings, ""])
    if math_findings:
        report_lines.extend(["### Math Analysis", "", math_findings, ""])
    if not writing_findings and not math_findings:
        report_lines.append("No findings from focused analysis.")

    combined_report = "\n".join(report_lines)

    # Write to disk
    run_dir = Path(state["run_dir"])
    run_dir.mkdir(parents=True, exist_ok=True)
    focus_file = run_dir / f"focus_{section_id.replace('/', '_')}.md"
    focus_file.write_text(combined_report, encoding="utf-8")

    return {"combined_report": combined_report}


# ── graph construction ──────────────────────────────────────────────


def build_focus_graph() -> StateGraph:
    """Build the focus subgraph."""
    builder = StateGraph(FocusState)

    builder.add_node("run_focused_writing_review", run_focused_writing_review)
    builder.add_node("run_focused_math_review", run_focused_math_review)
    builder.add_node("merge_focused_findings", merge_focused_findings)

    builder.set_entry_point("run_focused_writing_review")
    builder.add_edge("run_focused_writing_review", "run_focused_math_review")
    builder.add_edge("run_focused_math_review", "merge_focused_findings")
    builder.add_edge("merge_focused_findings", END)

    return builder


def compile_focus_graph():
    """Compile the focus graph ready for execution."""
    return build_focus_graph().compile()
