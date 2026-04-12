"""PDF → Markdown parser via MinerU / magic-pdf.

Supports two backends:

1. **magic-pdf 1.x** (``pip install "magic-pdf[full]"``): in-process
   ``UNIPipe`` pipeline — synchronous, no server needed.
2. **MinerU 2.x** (``pip install mineru``): falls back to the ``mineru``
   CLI since the 2.x Python API is server-mediated.

The parser auto-detects which backend is available.
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

from .base import BaseParser

_MAGIC_PDF_AVAILABLE: bool | None = None
_MINERU_CLI_AVAILABLE: bool | None = None


def _check_magic_pdf() -> bool:
    """Check if magic-pdf 1.x in-process API is importable."""
    global _MAGIC_PDF_AVAILABLE
    if _MAGIC_PDF_AVAILABLE is None:
        try:
            from magic_pdf.pipe.UNIPipe import UNIPipe as _  # noqa: F401
            _MAGIC_PDF_AVAILABLE = True
        except Exception:
            _MAGIC_PDF_AVAILABLE = False
    return _MAGIC_PDF_AVAILABLE


def _check_mineru_cli() -> bool:
    """Check if the ``mineru`` CLI is on PATH."""
    global _MINERU_CLI_AVAILABLE
    if _MINERU_CLI_AVAILABLE is None:
        _MINERU_CLI_AVAILABLE = shutil.which("mineru") is not None
    return _MINERU_CLI_AVAILABLE


# ── magic-pdf 1.x backend ─────────────────────────────────────────────


def _parse_with_magic_pdf(pdf_path: Path) -> str:
    """In-process conversion using magic-pdf 1.x UNIPipe."""
    from magic_pdf.config.make_content_config import DropMode, MakeMode
    from magic_pdf.data.data_reader_writer import (
        FileBasedDataReader,
        FileBasedDataWriter,
    )
    from magic_pdf.pipe.UNIPipe import UNIPipe

    with tempfile.TemporaryDirectory(prefix="revisica_mineru_") as tmp_dir:
        image_dir = str(Path(tmp_dir) / "images")
        Path(image_dir).mkdir()

        reader = FileBasedDataReader("")
        pdf_bytes = reader.read(str(pdf_path))
        image_writer = FileBasedDataWriter(image_dir)

        jso_useful_key: dict = {"_pdf_type": "", "model_list": []}
        pipe = UNIPipe(pdf_bytes, jso_useful_key, image_writer)
        pipe.pipe_classify()
        pipe.pipe_analyze()
        pipe.pipe_parse()

        md_content = pipe.pipe_mk_markdown(
            image_dir,
            drop_mode=DropMode.NONE,
            md_make_mode=MakeMode.MM_MD,
        )

        if isinstance(md_content, list):
            return "\n".join(md_content)
        return md_content


# ── MinerU 2.x CLI backend ────────────────────────────────────────────


def _parse_with_mineru_cli(pdf_path: Path) -> str:
    """Subprocess conversion using the ``mineru`` CLI (2.x)."""
    mineru_bin = shutil.which("mineru")
    if mineru_bin is None:
        raise RuntimeError("mineru CLI not found on PATH")

    with tempfile.TemporaryDirectory(prefix="revisica_mineru_") as tmp_dir:
        completed = subprocess.run(
            [
                mineru_bin,
                "-p", str(pdf_path),
                "-o", tmp_dir,
            ],
            capture_output=True,
            text=True,
            check=False,
            timeout=300,
        )

        if completed.returncode != 0:
            raise RuntimeError(
                f"mineru CLI failed (exit={completed.returncode}): "
                f"{completed.stderr}"
            )

        # MinerU writes <stem>/<stem>.md inside the output dir
        out_dir = Path(tmp_dir)
        for md_file in sorted(out_dir.rglob("*.md")):
            content = md_file.read_text(encoding="utf-8")
            if content.strip():
                return content

        raise RuntimeError(
            f"MinerU produced no Markdown output in {tmp_dir}"
        )


# ── parser class ───────────────────────────────────────────────────────


class MineruParser(BaseParser):
    """Convert PDF to Markdown using MinerU / magic-pdf.

    Prefers the in-process magic-pdf 1.x API when available; falls back
    to the ``mineru`` CLI for 2.x installations.
    """

    name = "mineru"

    def can_handle(self, path: Path) -> bool:
        return path.suffix.lower() == ".pdf"

    @classmethod
    def is_available(cls) -> bool:
        return _check_magic_pdf() or _check_mineru_cli()

    def parse(self, path: Path) -> str:
        if _check_magic_pdf():
            return _parse_with_magic_pdf(path)
        if _check_mineru_cli():
            return _parse_with_mineru_cli(path)
        raise RuntimeError(
            "MinerU is not available. Install one of:\n"
            '  pip install "magic-pdf[full]"   (1.x, in-process)\n'
            "  pip install mineru              (2.x, CLI-based)"
        )
