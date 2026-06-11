"""Final adjudication: a judge agent merges per-role findings into the
final Markdown report, with a deterministic fallback when it fails."""

from __future__ import annotations

import json
from pathlib import Path

from ..adjudication_policy import pick_preferred_item
from ..agents import get_agent, to_agent_spec
from ..bootstrap import PlatformStatus
from ..core_types import ProviderModelSpec, ReviewResult
from ..model_router import resolve_model_for_role
from ..providers.execution import run_provider_agent
from .artifacts import artifact_label
from .types import WritingRoleArtifact


def generate_final_report_agent(
    source: Path,
    run_dir: Path,
    venue_profile: str,
    platforms: dict[str, PlatformStatus],
    artifacts: list[WritingRoleArtifact],
    judge_spec: ProviderModelSpec | None,
    schema_path: str | None,
    timeout_seconds: int,
    warnings: list[str],
    codex_reasoning_effort: str | None = None,
) -> ReviewResult | None:
    """Generate final report using a real judge agent that reads findings files."""
    usable = [a for a in artifacts if a.result.success and a.findings is not None]
    if not usable:
        warnings.append("No writing-review role produced a usable structured output.")
        return None

    judge = judge_spec or default_judge_spec(usable)
    judge = resolve_model_for_role(judge, "judge")

    # Build file list for the judge to read
    findings_files = []
    for artifact in usable:
        base = f"{artifact.role}_{artifact_label(artifact.provider, artifact.model)}"
        json_path = run_dir / f"{base}.json"
        if json_path.exists():
            findings_files.append(str(json_path))

    agent_spec = to_agent_spec(get_agent("writing-judge"))
    task_prompt = (
        f"You are the final judge for a writing review.\n\n"
        f"Original LaTeX draft: `{source}`\n"
        f"Target venue profile: `{venue_profile}`\n\n"
        f"Read the original LaTeX file and then read these findings files:\n"
        + "\n".join(f"- `{fp}`" for fp in findings_files)
        + "\n\nMerge duplicates, keep only the strongest actionable points. "
        f"Produce a single Markdown report with sections: "
        f"Executive Summary, Basic Language Issues, Structure and Logic Issues, "
        f"Scholarly Rhetoric Issues, Venue-Style Gap, Suggested Rewrites, "
        f"Needs Human Check, Revision Priorities."
    )

    result = run_provider_agent(
        judge.provider,
        task_prompt,
        agent_spec,
        timeout_seconds,
        model=judge.model,
        working_dir=str(source.parent),
        codex_reasoning_effort=codex_reasoning_effort,
    )
    if result.success:
        return result

    warnings.append("Writing-review final adjudication failed, falling back to merged raw report.")
    return ReviewResult(
        provider=judge.provider,
        model=judge.model,
        command=[],
        returncode=0,
        output=fallback_final_report(usable, venue_profile),
        stderr="",
    )


def default_judge_spec(artifacts: list[WritingRoleArtifact]) -> ProviderModelSpec:
    selected = pick_preferred_item(
        artifacts,
        provider_getter=lambda artifact: artifact.provider,
    )
    return ProviderModelSpec(provider=selected.provider, model=selected.model)


def fallback_final_report(artifacts: list[WritingRoleArtifact], venue_profile: str) -> str:
    sections = [
        "# Executive Summary",
        "Writing-review adjudication failed. This fallback report preserves raw role outputs.",
        "",
        "## Basic Language Issues",
        "",
        "See raw role outputs below.",
        "",
        "## Structure and Logic Issues",
        "",
        "See raw role outputs below.",
        "",
        "## Scholarly Rhetoric Issues",
        "",
        "See raw role outputs below.",
        "",
        "## Venue-Style Gap",
        "",
        f"Target profile: `{venue_profile}`.",
        "",
        "## Suggested Rewrites",
        "",
        "Inspect raw role outputs for rewrite suggestions.",
        "",
        "## Needs Human Check",
        "",
        "The final judge did not complete successfully.",
        "",
        "## Revision Priorities",
        "",
        "1. Inspect raw role outputs below.",
        "",
        "## Raw Role Outputs",
        "",
    ]
    for artifact in artifacts:
        label = artifact.provider if not artifact.model else f"{artifact.provider}:{artifact.model}"
        sections.append(f"### {artifact.role} from {label}")
        sections.append("")
        sections.append("```json")
        sections.append(json.dumps(artifact.findings, indent=2, ensure_ascii=True))
        sections.append("```")
        sections.append("")
    return "\n".join(sections).strip() + "\n"
