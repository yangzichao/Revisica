"""Parse .tex files to Markdown via Pandoc subprocess."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from .base import BaseParser


def _pypandoc_binary_path() -> str | None:
    """Return the path to the pandoc binary shipped by `pypandoc-binary`.

    `pypandoc-binary` is pulled in via the `bundle` extra and ends up inside
    the frozen PyInstaller directory. On a user's machine with no Homebrew
    pandoc, this is the only pandoc available to the app.
    """
    try:
        import pypandoc
    except ImportError:
        return None
    try:
        path = pypandoc.get_pandoc_path()
    except OSError:
        return None
    return path or None


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
        if shutil.which("pandoc") is not None:
            return True
        return _pypandoc_binary_path() is not None

    def parse(self, path: Path) -> str:
        pandoc_path = shutil.which("pandoc") or _pypandoc_binary_path()
        if pandoc_path is None:
            raise RuntimeError(
                "Pandoc is required for .tex input but was not found on PATH "
                "or in the bundled pypandoc-binary package.\n"
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
