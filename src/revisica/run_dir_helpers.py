"""Helpers for populating a review run directory."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path


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
