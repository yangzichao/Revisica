"""On-disk persistence for job run snapshots.

Each run is one JSON file at ``<root>/<run_id>.json``, where ``<root>``
defaults to ``~/.revisica/jobs`` (next to ``api-token``) and can be
overridden via the ``REVISICA_JOBS_DIR`` environment variable — tests use
the override to isolate themselves, mirroring how parsed-document storage
handles ``REVISICA_PARSED_DOCUMENTS_DIR``.

Writes are atomic (temp file + ``os.replace``) so a crash mid-write never
leaves a truncated snapshot, and every failure here is logged-and-swallowed:
losing a history entry must never fail the job that produced it.
"""

from __future__ import annotations

import json
import logging
import os
import re
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

JOBS_DIR_ENV_VAR = "REVISICA_JOBS_DIR"
JOBS_DIR_NAME = "jobs"

# Run ids are uuid4 prefixes today, but they end up as filenames, so gate
# every lookup the same way parsed-document ids are gated.
_SAFE_RUN_ID_PATTERN = re.compile(r"^[A-Za-z0-9._-]+$")


def jobs_root() -> Path:
    """Return (and create) the directory holding run snapshots."""
    override = os.environ.get(JOBS_DIR_ENV_VAR, "").strip()
    root = (
        Path(override).expanduser()
        if override
        else Path.home() / ".revisica" / JOBS_DIR_NAME
    )
    root.mkdir(parents=True, exist_ok=True)
    return root


def _run_snapshot_path(run_id: str) -> Path:
    if not run_id or not _SAFE_RUN_ID_PATTERN.match(run_id):
        raise ValueError(f"Invalid run id: {run_id!r}")
    return jobs_root() / f"{run_id}.json"


def persist_run_snapshot(snapshot: dict[str, Any]) -> None:
    """Atomically write one run's snapshot. Never raises."""
    try:
        path = _run_snapshot_path(str(snapshot.get("run_id") or ""))
        temp_path = path.with_suffix(".json.tmp")
        temp_path.write_text(
            json.dumps(snapshot, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        os.replace(temp_path, path)
    except (OSError, ValueError, TypeError) as error:
        logger.warning("Failed to persist run snapshot: %s", error)


def load_all_run_snapshots() -> list[dict[str, Any]]:
    """Read every snapshot on disk, oldest ``started_at`` first.

    Corrupt or unreadable files are skipped with a warning — one bad
    snapshot must not block recovery of the rest.
    """
    snapshots: list[dict[str, Any]] = []
    for path in jobs_root().glob("*.json"):
        try:
            snapshot = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            logger.warning("Skipping unreadable run snapshot %s: %s", path, error)
            continue
        if isinstance(snapshot, dict) and snapshot.get("run_id"):
            snapshots.append(snapshot)
    snapshots.sort(key=lambda row: row.get("started_at") or "")
    return snapshots


def delete_run_snapshot(run_id: str) -> None:
    """Remove a run's snapshot file if present. Never raises."""
    try:
        _run_snapshot_path(run_id).unlink(missing_ok=True)
    except (OSError, ValueError) as error:
        logger.warning("Failed to delete run snapshot %s: %s", run_id, error)
