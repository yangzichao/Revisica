"""Polish subgraph — lightweight writing-only review.

This is the simplest graph: a single agent polishes the paper's prose.
No math checks, no cross-provider, no self-check.
"""

from __future__ import annotations

import functools
from datetime import datetime
from pathlib import Path

from langgraph.graph import END, StateGraph

from ..agents import get_agent, to_agent_spec
from ..bootstrap import detect_platforms
from ..core_types import ProviderModelSpec
from ..model_router import resolve_model_for_role
from ..review import _run_provider_agent
from .state import PolishState


# ── node functions ──────────────────────────────────────────────────


def read_paper(state: PolishState) -> dict:
    """Read the paper content from disk."""
    source_path = state["source_path"]
    content = Path(source_path).read_text(encoding="utf-8")
    return {"content": content}


def run_polish_agent(state: PolishState) -> dict:
    """Run the polish agent on the paper."""
    config = state["config"]
    source_path = state["source_path"]

    agent_spec = to_agent_spec(get_agent("polish-agent"))

    # Select provider and model
    providers = config.providers
    if not providers:
        platforms = detect_platforms()
        available_providers = [
            name for name, platform in platforms.items() if platform.available
        ]
        if not available_providers:
            return {
                "report": "",
                "warnings": ["No provider available for polish."],
            }
        providers = [ProviderModelSpec(provider=available_providers[0])]

    provider_spec = resolve_model_for_role(providers[0], "polish")
    platforms = detect_platforms()
    platform = platforms.get(provider_spec.provider)

    if platform is None or not platform.available:
        return {
            "report": "",
            "warnings": [f"Provider '{provider_spec.provider}' not available."],
        }

    task_prompt = f"Polish the academic draft at `{source_path}`. Read the file and suggest writing improvements."
    if config.custom_instructions:
        task_prompt += f"\n\nAdditional instructions: {config.custom_instructions}"

    result = _run_provider_agent(
        provider_name=provider_spec.provider,
        task_prompt=task_prompt,
        agent_spec=agent_spec,
        timeout_seconds=config.timeout_seconds,
        model=provider_spec.model,
        working_dir=str(Path(source_path).parent),
    )

    if result.success:
        return {"report": result.output}
    return {
        "report": result.output or "",
        "warnings": [f"Polish agent failed: {_format_agent_failure(result)}"],
    }


def _format_agent_failure(result) -> str:
    """Extract a useful failure snippet from a provider ReviewResult.

    CLI providers often print boilerplate banners at the top of stderr and
    the real error at the bottom (or on stdout). Showing the tail of the
    combined streams surfaces the actual error instead of the banner.
    """
    pieces: list[str] = []
    stderr = (result.stderr or "").strip()
    stdout = (result.output or "").strip()
    if stderr:
        pieces.append(stderr)
    if stdout and stdout != stderr:
        pieces.append(stdout)
    combined = "\n".join(pieces).strip()
    if not combined:
        return f"exit code {result.returncode} with no output"
    limit = 500
    if len(combined) <= limit:
        return combined
    return "…" + combined[-limit:]


def write_polish_report(state: PolishState) -> dict:
    """Write the polish report to disk."""
    run_dir = Path(state["run_dir"])
    run_dir.mkdir(parents=True, exist_ok=True)

    report_content = state.get("report", "")
    if not report_content:
        report_content = "No polish suggestions generated."

    (run_dir / "polish_report.md").write_text(report_content, encoding="utf-8")

    # Write summary
    source_path = state["source_path"]
    warnings = state.get("warnings", [])
    summary_lines = [
        "# Revisica Polish Report",
        "",
        f"- Source: `{source_path}`",
        f"- Timestamp: `{datetime.now().isoformat(timespec='seconds')}`",
        f"- Mode: `polish`",
        "",
        "## Report",
        "",
        f"See `polish_report.md`",
    ]
    if warnings:
        summary_lines.extend(["", "## Warnings", ""])
        for warning in warnings:
            summary_lines.append(f"- {warning}")

    (run_dir / "summary.md").write_text("\n".join(summary_lines) + "\n", encoding="utf-8")
    return {}


# ── graph construction ──────────────────────────────────────────────


def build_polish_graph() -> StateGraph:
    """Build the polish subgraph."""
    builder = StateGraph(PolishState)

    builder.add_node("read_paper", read_paper)
    builder.add_node("run_polish_agent", run_polish_agent)
    builder.add_node("write_polish_report", write_polish_report)

    builder.set_entry_point("read_paper")
    builder.add_edge("read_paper", "run_polish_agent")
    builder.add_edge("run_polish_agent", "write_polish_report")
    builder.add_edge("write_polish_report", END)

    return builder


@functools.cache
def compile_polish_graph():
    """Compile the polish graph ready for execution (cached)."""
    return build_polish_graph().compile()
