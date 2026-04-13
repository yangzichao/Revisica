from __future__ import annotations

import json
import logging
import re

from ..math_check import MathIssue, ProofBlueprint, ProofObligation


def extract_json_payload(text: str) -> dict[str, object] | None:
    stripped = text.strip()
    candidates = [stripped]
    fence_match = re.search(r"```json\s*(\{.*?\})\s*```", stripped, re.DOTALL)
    if fence_match:
        candidates.insert(0, fence_match.group(1))
    brace_match = re.search(r"(\{.*\})", stripped, re.DOTALL)
    if brace_match:
        candidates.append(brace_match.group(1))
    for candidate in candidates:
        try:
            parsed = json.loads(candidate)
        except Exception:
            logging.getLogger(__name__).debug("JSON parse attempt failed for candidate: %.120s", candidate)
            continue
        if isinstance(parsed, dict):
            return parsed
    return None


def extract_findings_payload(text: str) -> list[dict[str, object]] | None:
    payload = extract_json_payload(text)
    if payload is None:
        return None
    findings = payload.get("findings", [])
    if isinstance(findings, list):
        return findings
    return None


def _safe_step_index(finding: dict[str, object]) -> int | None:
    """Extract step_index as int, returning None for unparseable values.

    Falls back to searching for "Step N" in text fields if step_index is missing.
    """
    raw = finding.get("step_index")
    if raw is not None:
        try:
            return int(raw)
        except (ValueError, TypeError):
            pass

    # Fallback: search text fields for "Step N" pattern
    for key in ("rewrite", "title", "snippet", "explanation", "fix", "detail"):
        text = str(finding.get(key, ""))
        match = re.search(r"Step (\d+)", text)
        if match:
            return int(match.group(1))

    return None


def _find_obligation(
    obligations: list[ProofObligation],
    step_index: int,
) -> ProofObligation | None:
    for obligation in obligations:
        if obligation.step_index == step_index:
            return obligation
    return None


def parse_llm_math_issues(
    findings: list[dict[str, object]] | None,
    provider_name: str,
    model: str | None,
    blueprint: ProofBlueprint,
) -> list[MathIssue]:
    provider_label = provider_name if not model else f"{provider_name}:{model}"
    if findings is None:
        return [
            MathIssue(
                line_number=blueprint.proof.line_number if blueprint.proof is not None else blueprint.theorem.line_number,
                status="needs-human-check",
                severity="major",
                title=f"Unparseable LLM proof review from {provider_label}",
                snippet="provider output could not be parsed",
                explanation="The LLM proof reviewer returned output that could not be parsed as JSON.",
                fix="Inspect the raw provider output manually before relying on this proof review.",
                evidence=f"Provider `{provider_label}` returned non-JSON output for theorem line {blueprint.theorem.line_number}.",
            )
        ]

    issues: list[MathIssue] = []
    for finding in findings:
        if not isinstance(finding, dict):
            continue
        # Skip findings the LLM marked as correct/valid
        raw_verdict = str(finding.get("verdict", finding.get("status", "needs_human_check")))
        if raw_verdict.lower() in ("correct", "valid", "ok", "no_error"):
            continue
        step_index = _safe_step_index(finding)
        if step_index is None:
            continue
        obligation = _find_obligation(blueprint.obligations, step_index)
        snippet = obligation.text if obligation is not None else f"proof step {step_index}"
        # Accept both "verdict" and "status" field names from LLM output
        status = "llm-suspected" if raw_verdict.lower() in ("likely_error", "error", "incorrect", "wrong") else "needs-human-check"
        severity = str(finding.get("severity", "major"))
        issues.append(
            MathIssue(
                line_number=blueprint.proof.line_number if blueprint.proof is not None else blueprint.theorem.line_number,
                status=status,
                severity=severity,
                title=f"{provider_label} proof review: {finding.get('title', 'Suspicious proof step')}",
                snippet=snippet,
                explanation=str(finding.get("explanation", "The provider flagged this proof step as suspicious.")),
                fix=str(finding.get("fix", "Expand or verify this proof step manually.")),
                evidence=(
                    f"Provider `{provider_label}` flagged theorem line {blueprint.theorem.line_number}, "
                    f"step {step_index}."
                ),
            )
        )
    return issues


def parse_adjudicated_llm_math_issues(
    findings: list[dict[str, object]] | None,
    adjudicator_provider: str,
    adjudicator_model: str | None,
    blueprint: ProofBlueprint,
) -> list[MathIssue]:
    adjudicator_label = (
        adjudicator_provider if not adjudicator_model else f"{adjudicator_provider}:{adjudicator_model}"
    )
    if findings is None:
        return [
            MathIssue(
                line_number=blueprint.proof.line_number if blueprint.proof is not None else blueprint.theorem.line_number,
                status="needs-human-check",
                severity="major",
                title=f"Unparseable adjudicated proof review from {adjudicator_label}",
                snippet="adjudication output could not be parsed",
                explanation="The adjudicated proof review returned output that could not be parsed as JSON.",
                fix="Inspect the raw adjudication output manually.",
                evidence=f"Adjudicator `{adjudicator_label}` returned non-JSON output for theorem line {blueprint.theorem.line_number}.",
            )
        ]

    issues: list[MathIssue] = []
    for finding in findings:
        if not isinstance(finding, dict):
            continue
        step_index = _safe_step_index(finding)
        if step_index is None:
            continue
        obligation = _find_obligation(blueprint.obligations, step_index)
        snippet = obligation.text if obligation is not None else f"proof step {step_index}"
        verdict = str(finding.get("verdict", "needs_human_check"))
        status = "llm-suspected" if verdict == "likely_error" else "needs-human-check"
        providers = finding.get("providers", [])
        provider_text = ", ".join(providers) if isinstance(providers, list) and providers else adjudicator_label
        issues.append(
            MathIssue(
                line_number=blueprint.proof.line_number if blueprint.proof is not None else blueprint.theorem.line_number,
                status=status,
                severity=str(finding.get("severity", "major")),
                title=f"adjudicated proof review: {finding.get('title', 'Suspicious proof step')}",
                snippet=snippet,
                explanation=str(finding.get("explanation", "The adjudicator preserved this proof issue.")),
                fix=str(finding.get("fix", "Expand or verify this proof step manually.")),
                evidence=(
                    f"Adjudicated by `{adjudicator_label}` using provider findings from {provider_text} "
                    f"for theorem line {blueprint.theorem.line_number}, step {step_index}."
                ),
            )
        )
    return issues


def parse_self_checked_llm_math_issues(
    findings: list[dict[str, object]] | None,
    checker_provider: str,
    checker_model: str | None,
    reviewer_provider: str,
    reviewer_model: str | None,
    blueprint: ProofBlueprint,
) -> list[MathIssue]:
    checker_label = checker_provider if not checker_model else f"{checker_provider}:{checker_model}"
    reviewer_label = reviewer_provider if not reviewer_model else f"{reviewer_provider}:{reviewer_model}"
    if findings is None:
        return [
            MathIssue(
                line_number=blueprint.proof.line_number if blueprint.proof is not None else blueprint.theorem.line_number,
                status="needs-human-check",
                severity="major",
                title=f"Unparseable self-check proof review from {checker_label}",
                snippet="self-check output could not be parsed",
                explanation="The self-check proof review returned output that could not be parsed as JSON.",
                fix="Inspect the raw self-check output manually.",
                evidence=f"Self-checker `{checker_label}` returned non-JSON output for theorem line {blueprint.theorem.line_number}.",
            )
        ]

    issues: list[MathIssue] = []
    for finding in findings:
        if not isinstance(finding, dict):
            continue
        step_index = _safe_step_index(finding)
        if step_index is None:
            continue
        obligation = _find_obligation(blueprint.obligations, step_index)
        snippet = obligation.text if obligation is not None else f"proof step {step_index}"
        verdict = str(finding.get("verdict", "needs_human_check"))
        status = "llm-suspected" if verdict == "likely_error" else "needs-human-check"
        issues.append(
            MathIssue(
                line_number=blueprint.proof.line_number if blueprint.proof is not None else blueprint.theorem.line_number,
                status=status,
                severity=str(finding.get("severity", "major")),
                title=f"self-checked proof review: {finding.get('title', 'Suspicious proof step')}",
                snippet=snippet,
                explanation=str(finding.get("explanation", "The self-check preserved this proof issue.")),
                fix=str(finding.get("fix", "Expand or verify this proof step manually.")),
                evidence=(
                    f"Reviewed by `{reviewer_label}` and self-checked by `{checker_label}` "
                    f"for theorem line {blueprint.theorem.line_number}, step {step_index}."
                ),
            )
        )
    return issues
