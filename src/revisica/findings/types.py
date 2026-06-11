"""Unified, anchorable finding records shared by both review lanes.

A :class:`UnifiedFinding` is the lane-agnostic shape that writing-role
findings and math issues are converted into so the desktop app can render
them as inline annotations. Its :class:`FindingAnchor` locates the finding
in the *anchored document text* — the normalized markdown the review ran
against (persisted next to ``findings.json`` as ``document.md``).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

SEVERITY_LEVELS = ("critical", "major", "minor", "info")
_SEVERITY_RANK = {level: rank for rank, level in enumerate(SEVERITY_LEVELS)}

# How an anchor was resolved against the document text, strongest first.
RESOLUTION_EXACT = "exact"  # quote matched verbatim (whitespace-insensitive)
RESOLUTION_LINE = "line"  # only the reported line number could be trusted
RESOLUTION_UNRESOLVED = "unresolved"  # no usable location


def normalize_severity(raw: object) -> str:
    """Coerce reviewer-supplied severity strings onto SEVERITY_LEVELS."""
    text = str(raw or "").strip().lower()
    if text in _SEVERITY_RANK:
        return text
    if text in ("blocker", "high", "error"):
        return "critical"
    if text in ("medium", "warning", "moderate"):
        return "major"
    if text in ("low", "trivial", "nit", "suggestion"):
        return "minor"
    return "major"


def severity_rank(severity: str) -> int:
    return _SEVERITY_RANK.get(severity, _SEVERITY_RANK["major"])


@dataclass
class FindingAnchor:
    quote: str
    line_number: int | None = None  # 1-based line in the anchored document
    start_offset: int | None = None  # char offsets into the anchored document
    end_offset: int | None = None
    section_id: str | None = None
    section_title: str | None = None
    resolution: str = RESOLUTION_UNRESOLVED


@dataclass
class UnifiedFinding:
    id: str
    lane: str  # "writing" | "math"
    role: str  # writing role name, or "deterministic" / "llm-proof"
    provider: str | None
    model: str | None
    category: str
    severity: str
    title: str
    explanation: str
    fix: str
    evidence: str
    status: str | None  # math statuses such as "machine-refuted"
    anchor: FindingAnchor

    def to_dict(self) -> dict[str, object]:
        return asdict(self)
