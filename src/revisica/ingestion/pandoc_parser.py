"""Parse .tex files to Markdown via Pandoc subprocess."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from .base import BaseParser


class PandocParser(BaseParser):
    """Convert LaTeX to Markdown using Pandoc.

    Pandoc expands most LaTeX macros and produces clean Markdown with
    LaTeX math blocks preserved.  This is the preferred parser for .tex
    input when Pandoc is installed.
    """

    name = "pandoc"

    def can_handle(self, path: Path) -> bool:
        return path.suffix.lower() == ".tex"

    @classmethod
    def is_available(cls) -> bool:
        return shutil.which("pandoc") is not None

    def parse(self, path: Path) -> str:
        pandoc_path = shutil.which("pandoc")
        if pandoc_path is None:
            raise RuntimeError(
                "Pandoc is required for .tex input but was not found on PATH.\n"
                "Install: brew install pandoc (macOS) or apt install pandoc (Linux)"
            )

        # Pass `path.name` with `cwd=path.parent` so Pandoc resolves \input{}
        # and \include{} relative to the .tex file's own directory, not the
        # caller's CWD.
        completed = subprocess.run(
            [
                pandoc_path,
                path.name,
                "--from=latex",
                "--to=markdown",
                "--wrap=none",
                "--standalone",
            ],
            capture_output=True,
            text=True,
            check=False,
            timeout=60,
            cwd=path.parent,
        )

        if completed.returncode != 0:
            raise RuntimeError(
                f"Pandoc failed (exit={completed.returncode}): {completed.stderr}"
            )

        return completed.stdout
