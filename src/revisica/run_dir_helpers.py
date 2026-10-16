"""Helpers for populating a review run directory."""

from __future__ import annotations

import os
import shutil
import sys
from datetime import datetime
from pathlib import Path

REVIEWS_DIR_ENV_VAR = "REVISICA_REVIEWS_DIR"


def reviews_root() -> Path:
    """Directory that holds review runs created without an explicit output dir.

    Honors ``REVISICA_REVIEWS_DIR`` first. The desktop app sets it to its
    userData folder: its backend runs with the app bundle's Resources dir
    as cwd, so ``<cwd>/reviews`` put every review inside Revisica.app,
    where an app update replaces it. Falls back to ``<cwd>/reviews`` for
    CLI use.
    """
    override = os.environ.get(REVIEWS_DIR_ENV_VAR, "").strip()
    return Path(override).expanduser() if override else Path.cwd() / "reviews"


def create_review_run_dir(name_prefix: str) -> Path:
    """Create ``<reviews root>/<name_prefix>-<timestamp>``, never reusing one.

    Two runs of the same paper started within the same second used to get
    the same directory and overwrite each other's artifacts; the second one
    now gets a ``-2`` suffix.
    """
    root = reviews_root()
    root.mkdir(parents=True, exist_ok=True)
    base_name = f"{name_prefix}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    candidate = root / base_name
    suffix = 2
    while True:
        try:
            candidate.mkdir()
            return candidate
        except FileExistsError:
            candidate = root / f"{base_name}-{suffix}"
            suffix += 1


def copy_source_into_run_dir(source: Path, run_dir: Path) -> Path | None:
    """Copy the original input document into the review run directory.

    Reviewers and users want the source paper sitting next to the review
    outputs for easy cross-reference. If the copy fails (disk full,
    permission error), log a warning and return None — the review itself
    should still proceed.
    """
    destination = run_dir / source.name
    try:
        if destination.exists() and destination.resolve() == source.resolve():
            return destination
    except OSError:
        pass
    try:
        shutil.copy2(source, destination)
    except OSError as err:
        print(
            f"[revisica] warning: could not copy source '{source}' into '{run_dir}': {err}",
            file=sys.stderr,
        )
        return None
    return destination
