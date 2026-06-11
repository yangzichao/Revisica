"""On-disk artifacts for a writing review run: per-role outputs, the
final report, and the human-readable summary."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from ..core_types import ProviderModelSpec, ReviewResult
from .types import MATH_VERIFICATION_ROLES, WRITING_ROLES, WritingRoleArtifact


def artifact_label(provider: str, model: str | None) -> str:
    if not model:
        return provider
    cleaned = "".join(char if char.isalnum() else "_" for char in model).strip("_")
    return f"{provider}_{cleaned}" if cleaned else provider


def write_role_artifact(run_dir: Path, artifact: WritingRoleArtifact) -> None:
    base = f"{artifact.role}_{artifact_label(artifact.provider, artifact.model)}"
    (run_dir / f"{base}.md").write_text(artifact.result.output, encoding="utf-8")
    metadata = {
        "role": artifact.role,
        "provider": artifact.provider,
        "model": artifact.model,
        "returncode": artifact.result.returncode,
        "success": artifact.result.success,
        "findings": artifact.findings,
    }
    (run_dir / f"{base}.json").write_text(
        json.dumps(metadata, indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )
    if artifact.result.stderr.strip():
        (run_dir / f"{base}.stderr.txt").write_text(artifact.result.stderr, encoding="utf-8")


def write_final_report(run_dir: Path, result: ReviewResult) -> None:
    (run_dir / "final_report.md").write_text(result.output, encoding="utf-8")
    payload = {
        "provider": result.provider,
        "model": result.model,
        "returncode": result.returncode,
        "success": result.success,
        "command": result.command,
    }
    (run_dir / "final_report.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )
    if result.stderr.strip():
        (run_dir / "final_report.stderr.txt").write_text(result.stderr, encoding="utf-8")


def write_summary(
    run_dir: Path,
    source: Path,
    venue_profile: str,
    detected_providers: list[str],
    reviewer_specs: list[ProviderModelSpec],
    judge_spec: ProviderModelSpec | None,
    mode: str,
    artifacts: list[WritingRoleArtifact],
    final_report: ReviewResult | None,
    warnings: list[str],
) -> None:
    all_roles = list(WRITING_ROLES) + list(MATH_VERIFICATION_ROLES)
    issues_by_role: dict[str, int] = {role: 0 for role in all_roles}
    for artifact in artifacts:
        if artifact.findings is not None:
            issues_by_role.setdefault(artifact.role, 0)
            issues_by_role[artifact.role] += len(artifact.findings)

    # Count section cross-check and claim verification findings
    section_xcheck_count = sum(
        len(a.findings) for a in artifacts
        if a.role.startswith("section-xcheck-") and a.findings is not None
    )

    lines = [
        "# Revisica Writing Review Run",
        "",
        f"- Source: `{source}`",
        f"- Timestamp: `{datetime.now().isoformat(timespec='seconds')}`",
        f"- Venue profile: `{venue_profile}`",
        f"- Detected providers: `{', '.join(detected_providers) if detected_providers else 'none'}`",
        f"- Reviewers: `{', '.join(spec.label for spec in reviewer_specs)}`",
        f"- Judge: `{judge_spec.label if judge_spec is not None else 'auto'}`",
        f"- Mode: `{mode}`",
        f"- Basic findings: `{issues_by_role['basic']}`",
        f"- Structure findings: `{issues_by_role['structure']}`",
        f"- Venue findings: `{issues_by_role['venue']}`",
        f"- Math-claim-verifier findings: `{issues_by_role.get('math-claim-verifier', 0)}`",
        f"- Notation-tracker findings: `{issues_by_role.get('notation-tracker', 0)}`",
        f"- Formula-cross-checker findings: `{issues_by_role.get('formula-cross-checker', 0)}`",
        f"- Section cross-check findings: `{section_xcheck_count}`",
        f"- Claim verification findings: `{sum(len(a.findings) for a in artifacts if a.role.startswith('claim-verify-') and a.findings is not None)}`",
        "",
        "## Role Runs",
        "",
    ]
    for artifact in artifacts:
        status = "ok" if artifact.result.success else "failed"
        label = artifact.provider if not artifact.model else f"{artifact.provider}:{artifact.model}"
        lines.append(f"- `{artifact.role}` via `{label}`: {status} (exit={artifact.result.returncode})")
    if warnings:
        lines.extend(["", "## Warnings", ""])
        for warning in warnings:
            lines.append(f"- {warning}")
    lines.extend(["", "## Files", ""])
    for artifact in artifacts:
        base = f"{artifact.role}_{artifact_label(artifact.provider, artifact.model)}"
        lines.append(f"- `{base}.md`")
        lines.append(f"- `{base}.json`")
        if artifact.result.stderr.strip():
            lines.append(f"- `{base}.stderr.txt`")
    if final_report is not None:
        lines.append("- `final_report.md`")
        lines.append("- `final_report.json`")
        if final_report.stderr.strip():
            lines.append("- `final_report.stderr.txt`")
    (run_dir / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
