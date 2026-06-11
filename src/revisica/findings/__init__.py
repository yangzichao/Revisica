"""Unified, anchorable findings for inline annotations.

- ``types``   — :class:`UnifiedFinding` / :class:`FindingAnchor` records
- ``collect`` — convert writing-role dicts + math issues into findings
- ``anchor``  — quote-first anchor resolution against the document text
- ``persist`` — ``findings.json`` + ``document.md`` in the run directory
"""

from .anchor import resolve_anchors
from .collect import collect_unified_findings
from .persist import (
    DOCUMENT_FILENAME,
    FINDINGS_FILENAME,
    load_findings_payload,
    write_findings_artifacts,
)
from .types import FindingAnchor, UnifiedFinding, normalize_severity

__all__ = [
    "DOCUMENT_FILENAME",
    "FINDINGS_FILENAME",
    "FindingAnchor",
    "UnifiedFinding",
    "collect_unified_findings",
    "load_findings_payload",
    "normalize_severity",
    "resolve_anchors",
    "write_findings_artifacts",
]
