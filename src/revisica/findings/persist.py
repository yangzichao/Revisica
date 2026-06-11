"""Read/write the findings artifact pair in a unified run directory.

``findings.json`` holds the anchored :class:`UnifiedFinding` records;
``document.md`` is the exact document text the anchors index into (the
normalized markdown the review ran against). They are written together so
a consumer can always re-resolve offsets against the right text.
"""

from __future__ import annotations

import json
from pathlib import Path

from .types import UnifiedFinding

FINDINGS_FILENAME = "findings.json"
DOCUMENT_FILENAME = "document.md"
FINDINGS_SCHEMA_VERSION = 1


def write_findings_artifacts(
    run_dir: Path,
    findings: list[UnifiedFinding],
    document_text: str,
) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "version": FINDINGS_SCHEMA_VERSION,
        "document_file": DOCUMENT_FILENAME,
        "count": len(findings),
        "findings": [finding.to_dict() for finding in findings],
    }
    (run_dir / FINDINGS_FILENAME).write_text(
        json.dumps(payload, indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )
    (run_dir / DOCUMENT_FILENAME).write_text(document_text, encoding="utf-8")


def load_findings_payload(run_dir: Path) -> dict[str, object] | None:
    """Load findings.json plus the anchored document text, or None.

    Returns ``None`` when the run predates the findings artifact or the
    file is unreadable — callers treat both as "no annotations available".
    """
    findings_path = run_dir / FINDINGS_FILENAME
    if not findings_path.exists():
        return None
    try:
        payload = json.loads(findings_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(payload, dict):
        return None
    document_path = run_dir / str(payload.get("document_file") or DOCUMENT_FILENAME)
    document_text = ""
    if document_path.exists():
        try:
            document_text = document_path.read_text(encoding="utf-8")
        except OSError:
            document_text = ""
    payload["document_markdown"] = document_text
    return payload
