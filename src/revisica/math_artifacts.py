from __future__ import annotations

from dataclasses import asdict
from datetime import datetime
import json
from pathlib import Path

from .math_extraction import compact_text
from .math_types import (
    FunctionDefinition,
    LLMAdjudicationArtifact,
    LLMProofReviewArtifact,
    LLMSelfCheckArtifact,
    MathClaim,
    MathIssue,
    ProofBlueprint,
    ProofBlock,
    TheoremBlock,
)


def write_math_artifacts(
    run_dir: Path,
    source: Path,
    functions: list[FunctionDefinition],
    claims: list[MathClaim],
    theorems: list[TheoremBlock],
    proofs: list[ProofBlock],
    blueprints: list[ProofBlueprint],
    issues: list[MathIssue],
    llm_provider_results: list[LLMProofReviewArtifact],
    llm_self_check_results: list[LLMSelfCheckArtifact],
    llm_adjudication_results: list[LLMAdjudicationArtifact],
    warnings: list[str],
) -> None:
    payload = {
        "source": str(source),
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "functions": [asdict(item) | {"expression": str(item.expression)} for item in functions],
        "claims": [asdict(item) for item in claims],
        "theorems": [asdict(item) for item in theorems],
        "proofs": [asdict(item) for item in proofs],
        "blueprints": [asdict(item) for item in blueprints],
        "issues": [asdict(item) for item in issues],
        "llm_provider_results": [
            {
                "provider": item.provider,
                "model": item.model,
                "theorem_line_number": item.theorem_line_number,
                "returncode": item.result.returncode,
                "success": item.result.success,
                "findings": item.findings,
            }
            for item in llm_provider_results
        ],
        "llm_self_check_results": [
            {
                "provider": item.provider,
                "model": item.model,
                "theorem_line_number": item.theorem_line_number,
                "returncode": item.result.returncode,
                "success": item.result.success,
                "findings": item.findings,
            }
            for item in llm_self_check_results
        ],
        "llm_adjudication_results": [
            {
                "adjudicator_provider": item.adjudicator_provider,
                "model": item.model,
                "theorem_line_number": item.theorem_line_number,
                "returncode": item.result.returncode,
                "success": item.result.success,
                "findings": item.findings,
            }
            for item in llm_adjudication_results
        ],
        "warnings": warnings,
    }
    (run_dir / "math_report.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )
    (run_dir / "math_report.md").write_text(
        render_math_report(source, functions, claims, blueprints, issues),
        encoding="utf-8",
    )
    (run_dir / "summary.md").write_text(
        render_summary(
            source,
            functions,
            claims,
            blueprints,
            issues,
            warnings,
            llm_provider_results,
            llm_self_check_results,
            llm_adjudication_results,
        ),
        encoding="utf-8",
    )
    for index, artifact in enumerate(llm_provider_results, start=1):
        filename = f"llm_proof_review_{index}_{artifact.provider}_theorem_{artifact.theorem_line_number}.md"
        (run_dir / filename).write_text(artifact.result.output, encoding="utf-8")
        if artifact.result.stderr.strip():
            (run_dir / filename.replace(".md", ".stderr.txt")).write_text(
                artifact.result.stderr,
                encoding="utf-8",
            )
    for index, artifact in enumerate(llm_self_check_results, start=1):
        filename = f"llm_proof_self_check_{index}_{artifact.provider}_theorem_{artifact.theorem_line_number}.md"
        (run_dir / filename).write_text(artifact.result.output, encoding="utf-8")
        if artifact.result.stderr.strip():
            (run_dir / filename.replace(".md", ".stderr.txt")).write_text(
                artifact.result.stderr,
                encoding="utf-8",
            )
    for index, artifact in enumerate(llm_adjudication_results, start=1):
        filename = (
            f"llm_proof_adjudication_{index}_{artifact.adjudicator_provider}"
            f"_theorem_{artifact.theorem_line_number}.md"
        )
        (run_dir / filename).write_text(artifact.result.output, encoding="utf-8")
        if artifact.result.stderr.strip():
            (run_dir / filename.replace(".md", ".stderr.txt")).write_text(
                artifact.result.stderr,
                encoding="utf-8",
            )


def render_math_report(
    source: Path,
    functions: list[FunctionDefinition],
    claims: list[MathClaim],
    blueprints: list[ProofBlueprint],
    issues: list[MathIssue],
) -> str:
    refuted = [item for item in issues if item.status == "machine-refuted"]
    verified = [item for item in issues if item.status == "machine-verified"]
    llm_suspected = [item for item in issues if item.status == "llm-suspected"]
    manual = [item for item in issues if item.status == "needs-human-check"]
    lines = [
        f"# Math Review of `{source.name}`",
        "",
        "## Executive Summary",
        "",
        (
            f"Revisica extracted {len(functions)} function definitions and {len(claims)} "
            f"math-related claims, plus {len(blueprints)} theorem/proof blueprint(s). "
            f"It machine-refuted {len(refuted)} claim(s), "
            f"machine-verified {len(verified)} claim(s), flagged {len(llm_suspected)} "
            f"LLM-suspected issue(s), and left {len(manual)} claim(s) "
            "for human follow-up."
        ),
        "",
        "## Blueprint-Lite",
        "",
    ]
    if blueprints:
        for blueprint in blueprints:
            lines.extend(_render_blueprint(blueprint))
    else:
        lines.append("No theorem/proof environments were extracted.")

    lines.extend(["", "## Machine Refuted Claims", ""])
    if refuted:
        for issue in refuted:
            lines.extend(_render_issue(issue))
    else:
        lines.append("No machine-refuted claims.")

    lines.extend(["", "## Machine Verified Claims", ""])
    if verified:
        for issue in verified:
            lines.extend(_render_issue(issue))
    else:
        lines.append("No machine-verified claims.")

    lines.extend(["", "## LLM-Suspected Proof Issues", ""])
    if llm_suspected:
        for issue in llm_suspected:
            lines.extend(_render_issue(issue))
    else:
        lines.append("No LLM-suspected proof issues.")

    lines.extend(["", "## Needs Human Check", ""])
    if manual:
        for issue in manual:
            lines.extend(_render_issue(issue))
    else:
        lines.append("No unresolved math claims.")

    lines.extend(["", "## Suggested Revision Order", ""])
    if refuted:
        for index, issue in enumerate(refuted, start=1):
            lines.append(f"{index}. {issue.title}")
    else:
        lines.append("1. No refuted claims were found automatically.")

    return "\n".join(lines) + "\n"


def render_summary(
    source: Path,
    functions: list[FunctionDefinition],
    claims: list[MathClaim],
    blueprints: list[ProofBlueprint],
    issues: list[MathIssue],
    warnings: list[str],
    llm_provider_results: list[LLMProofReviewArtifact],
    llm_self_check_results: list[LLMSelfCheckArtifact],
    llm_adjudication_results: list[LLMAdjudicationArtifact],
) -> str:
    refuted = sum(1 for item in issues if item.status == "machine-refuted")
    verified = sum(1 for item in issues if item.status == "machine-verified")
    llm_suspected = sum(1 for item in issues if item.status == "llm-suspected")
    manual = sum(1 for item in issues if item.status == "needs-human-check")
    lines = [
        "# Revisica Math Run",
        "",
        f"- Source: `{source}`",
        f"- Timestamp: `{datetime.now().isoformat(timespec='seconds')}`",
        f"- Function definitions: `{len(functions)}`",
        f"- Claims extracted: `{len(claims)}`",
        f"- Theorem/proof blueprints: `{len(blueprints)}`",
        f"- Machine refuted: `{refuted}`",
        f"- Machine verified: `{verified}`",
        f"- LLM-suspected: `{llm_suspected}`",
        f"- Needs human check: `{manual}`",
        f"- Raw LLM proof reviews: `{len(llm_provider_results)}`",
        f"- LLM self-checks: `{len(llm_self_check_results)}`",
        f"- LLM adjudications: `{len(llm_adjudication_results)}`",
        "",
    ]
    if warnings:
        lines.extend(["## Warnings", ""])
        for warning in warnings:
            lines.append(f"- {warning}")
        lines.append("")

    lines.extend(["## Files", "", "- `math_report.md`", "- `math_report.json`"])
    for index, artifact in enumerate(llm_provider_results, start=1):
        lines.append(
            f"- `llm_proof_review_{index}_{artifact.provider}_theorem_{artifact.theorem_line_number}.md`"
        )
    for index, artifact in enumerate(llm_self_check_results, start=1):
        lines.append(
            f"- `llm_proof_self_check_{index}_{artifact.provider}_theorem_{artifact.theorem_line_number}.md`"
        )
    for index, artifact in enumerate(llm_adjudication_results, start=1):
        lines.append(
            f"- `llm_proof_adjudication_{index}_{artifact.adjudicator_provider}_theorem_{artifact.theorem_line_number}.md`"
        )
    return "\n".join(lines) + "\n"


def _render_issue(issue: MathIssue) -> list[str]:
    return [
        f"### {issue.title}",
        "",
        f"- Line: `{issue.line_number}`",
        f"- Status: `{issue.status}`",
        f"- Severity: `{issue.severity}`",
        f"- Snippet: `{issue.snippet}`",
        f"- Why: {issue.explanation}",
        f"- Fix: {issue.fix}",
        f"- Evidence: {issue.evidence}",
        "",
    ]


def _render_blueprint(blueprint: ProofBlueprint) -> list[str]:
    theorem = blueprint.theorem
    title = theorem.title or theorem.env_name.title()
    lines = [
        f"### {title}",
        "",
        f"- Theorem line: `{theorem.line_number}`",
        f"- Theorem type: `{theorem.env_name}`",
        f"- Statement: `{compact_text(theorem.statement)}`",
    ]
    if blueprint.proof is None:
        lines.append("- Proof: `missing`")
        lines.append("- Obligations: `0`")
        lines.append("")
        return lines

    lines.append(f"- Proof line: `{blueprint.proof.line_number}`")
    lines.append(f"- Obligations: `{len(blueprint.obligations)}`")
    if blueprint.obligations:
        lines.append("- Extracted obligations:")
        for obligation in blueprint.obligations:
            lines.append(
                f"  {obligation.step_index}. [{obligation.obligation_type}] "
                f"`{compact_text(obligation.text)}`"
            )
    lines.append("")
    return lines
