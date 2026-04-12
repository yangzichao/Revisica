"""PDF → Markdown parser via MinerU CLI.

Install: ``pip install mineru`` (requires GPU or Apple MPS).
The ``mineru`` CLI works across both 1.x and 2.x versions.
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

from .base import BaseParser


class MineruParser(BaseParser):
    """Convert PDF to Markdown using the ``mineru`` CLI."""

    name = "mineru"

    def can_handle(self, path: Path) -> bool:
        return path.suffix.lower() == ".pdf"

    @classmethod
    def is_available(cls) -> bool:
        return shutil.which("mineru") is not None

    def parse(self, path: Path) -> str:
        mineru_bin = shutil.which("mineru")
        if mineru_bin is None:
            raise RuntimeError(
                "MinerU is not installed. Install with:\n"
                "  pip install mineru"
            )

        with tempfile.TemporaryDirectory(prefix="revisica_mineru_") as tmp_dir:
            completed = subprocess.run(
                [mineru_bin, "-p", str(path), "-o", tmp_dir],
                capture_output=True,
                text=True,
                check=False,
                timeout=300,
            )

            if completed.returncode != 0:
                raise RuntimeError(
                    f"mineru failed (exit={completed.returncode}): "
                    f"{completed.stderr}"
                )

            # MinerU writes <stem>/<stem>.md inside the output dir
            for md_file in sorted(Path(tmp_dir).rglob("*.md")):
                content = md_file.read_text(encoding="utf-8")
                if content.strip():
                    return content

            raise RuntimeError(
                f"MinerU produced no Markdown output in {tmp_dir}"
            )
