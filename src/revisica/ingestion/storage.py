"""Persistence for parsed documents.

Each successful parse is written to ``parsed-documents/<id>/`` under the
current working directory. Layout mirrors ``reviews/<id>/`` so artefacts
sit side by side.

Directory contents:
  - ``document.json`` — manifest (id, timestamps, source, parser, elapsed, full
    ``RevisicaDocument`` under ``document`` key).
  - ``normalized.md`` — just ``document.markdown``, used when a later review
    run wants to skip the parse step and re-feed the already-normalized
    markdown into the pipeline via the markdown passthrough parser.
"""

from __future__ import annotations

import json
import re
import shutil
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .types import RevisicaDocument


PARSED_DOCUMENTS_DIR_NAME = "parsed-documents"
DOCUMENT_MANIFEST_FILENAME = "document.json"
NORMALIZED_MARKDOWN_FILENAME = "normalized.md"

# Ids are constructed from user-supplied filenames + parser + timestamp,
# and are later used as path segments. This regex gates every lookup so a
# crafted id can't traverse outside parsed-documents/.
_SAFE_ID_PATTERN = re.compile(r"^[A-Za-z0-9._-]+$")

# Any character that isn't alphanumeric, dot, underscore, or dash gets
# replaced with a dash when deriving the ``<stem>`` portion of an id.
_UNSAFE_STEM_CHARS = re.compile(r"[^A-Za-z0-9._-]+")


def parsed_documents_root() -> Path:
    """Return (and create) the root directory for saved parses."""
    root = Path.cwd() / PARSED_DOCUMENTS_DIR_NAME
    root.mkdir(parents=True, exist_ok=True)
    return root


def make_parsed_document_id(source_path: str, parser_used: str) -> str:
    """Build a filesystem-safe id of the form ``<stem>-<parser>-<timestamp>``."""
    stem = Path(source_path).stem or "document"
    safe_stem = _UNSAFE_STEM_CHARS.sub("-", stem).strip("-") or "document"
    safe_parser = _UNSAFE_STEM_CHARS.sub("-", parser_used).strip("-") or "unknown"
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return f"{safe_stem}-{safe_parser}-{timestamp}"


def _ensure_safe_id(parsed_document_id: str) -> str:
    """Reject ids that could escape the parsed-documents/ directory."""
    if not parsed_document_id or not _SAFE_ID_PATTERN.match(parsed_document_id):
        raise ValueError(f"Invalid parsed document id: {parsed_document_id!r}")
    return parsed_document_id


def parsed_document_dir(parsed_document_id: str) -> Path:
    """Return the on-disk directory for a parsed document id."""
    safe_id = _ensure_safe_id(parsed_document_id)
    return parsed_documents_root() / safe_id


def normalized_markdown_path(parsed_document_id: str) -> Path:
    """Return the path to the normalized.md file for a parsed document."""
    return parsed_document_dir(parsed_document_id) / NORMALIZED_MARKDOWN_FILENAME


def save_parsed_document(
    document: RevisicaDocument,
    elapsed_ms: int,
) -> dict[str, Any]:
    """Write manifest + normalized markdown for ``document``.

    Returns the manifest dict, including the generated ``id``.
    """
    parsed_document_id = make_parsed_document_id(
        document.source_path,
        document.parser_used,
    )
    target_dir = parsed_document_dir(parsed_document_id)
    target_dir.mkdir(parents=True, exist_ok=True)

    parsed_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    manifest: dict[str, Any] = {
        "id": parsed_document_id,
        "parsed_at": parsed_at,
        "source_path": document.source_path,
        "parser_used": document.parser_used,
        "elapsed_ms": int(elapsed_ms),
        "document": asdict(document),
    }

    manifest_path = target_dir / DOCUMENT_MANIFEST_FILENAME
    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    markdown_path = target_dir / NORMALIZED_MARKDOWN_FILENAME
    markdown_path.write_text(document.markdown, encoding="utf-8")

    return manifest


def load_parsed_document(parsed_document_id: str) -> dict[str, Any]:
    """Load the manifest for a saved parse. Raises ``FileNotFoundError``."""
    manifest_path = parsed_document_dir(parsed_document_id) / DOCUMENT_MANIFEST_FILENAME
    if not manifest_path.exists():
        raise FileNotFoundError(
            f"No parsed document found with id {parsed_document_id!r}"
        )
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def list_parsed_documents() -> list[dict[str, Any]]:
    """Scan the root directory and return summary rows, newest first."""
    root = parsed_documents_root()
    summaries: list[dict[str, Any]] = []
    for child in root.iterdir():
        if not child.is_dir():
            continue
        manifest_path = child / DOCUMENT_MANIFEST_FILENAME
        if not manifest_path.exists():
            continue
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        document = manifest.get("document") or {}
        metadata = document.get("metadata") or {}
        summaries.append({
            "id": manifest.get("id", child.name),
            "parsed_at": manifest.get("parsed_at"),
            "source_path": manifest.get("source_path"),
            "parser_used": manifest.get("parser_used"),
            "elapsed_ms": manifest.get("elapsed_ms"),
            "title": metadata.get("title", ""),
            "authors": metadata.get("authors", []),
            "section_count": len(document.get("sections", [])),
        })
    summaries.sort(key=lambda row: row.get("parsed_at") or "", reverse=True)
    return summaries


def delete_parsed_document(parsed_document_id: str) -> None:
    """Remove a saved parse directory. Raises ``FileNotFoundError`` if missing."""
    target_dir = parsed_document_dir(parsed_document_id)
    if not target_dir.exists():
        raise FileNotFoundError(
            f"No parsed document found with id {parsed_document_id!r}"
        )
    shutil.rmtree(target_dir)
