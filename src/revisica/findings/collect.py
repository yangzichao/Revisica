"""Convert lane-specific results into :class:`UnifiedFinding` records.

Writing-role findings arrive as loosely-typed dicts (the agents return
JSON), math issues as :class:`MathIssue` dataclasses; both are mapped onto
the one shape the annotation pipeline understands. Anchors start out
unresolved — ``anchor.resolve_anchors`` fills in offsets and sections.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .types import FindingAnchor, UnifiedFinding, normalize_severity

if TYPE_CHECKING:
    from ..math_check.types import MathReviewRun
    from ..writing.types import WritingReviewRun


def collect_unified_findings(
    writing: "WritingReviewRun | None",
    math: "MathReviewRun | None",
) -> list[UnifiedFinding]:
    findings: list[UnifiedFinding] = []
    if writing is not None:
        for artifact in writing.artifacts:
            for raw in artifact.findings or []:
                if not isinstance(raw, dict):
                    continue
                findings.append(_from_writing_finding(artifact, raw))
    if math is not None:
        for issue in math.issues:
            findings.append(_from_math_issue(issue))
    for index, finding in enumerate(findings, start=1):
        finding.id = f"f-{index:03d}"
    return findings


def _text(raw: dict[str, object], key: str) -> str:
    value = raw.get(key)
    return str(value).strip() if value is not None else ""


def _from_writing_finding(artifact, raw: dict[str, object]) -> UnifiedFinding:
    return UnifiedFinding(
        id="",
        lane="writing",
        role=artifact.role,
        provider=artifact.provider,
        model=artifact.model,
        category=_text(raw, "category") or artifact.role,
        severity=normalize_severity(raw.get("severity")),
        title=_text(raw, "title") or "(untitled finding)",
        explanation=_text(raw, "explanation"),
        fix=_text(raw, "fix") or _text(raw, "rewrite"),
        evidence="",
        status=None,
        anchor=FindingAnchor(quote=_text(raw, "snippet")),
    )


def _math_role(status: str) -> str:
    if status.startswith("machine"):
        return "deterministic"
    if status.startswith("llm"):
        return "llm-proof"
    return "math"


def _from_math_issue(issue) -> UnifiedFinding:
    return UnifiedFinding(
        id="",
        lane="math",
        role=_math_role(issue.status),
        provider=None,
        model=None,
        category="math",
        severity=normalize_severity(issue.severity),
        title=issue.title or "(untitled finding)",
        explanation=issue.explanation,
        fix=issue.fix,
        evidence=issue.evidence,
        status=issue.status,
        anchor=FindingAnchor(
            quote=issue.snippet,
            line_number=issue.line_number if issue.line_number > 0 else None,
        ),
    )
