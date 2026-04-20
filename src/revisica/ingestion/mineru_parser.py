"""PDF → Markdown parser via MinerU CLI.

Install: ``pip install 'mineru[all]'``. The ``[all]`` extra is platform-aware
and pulls the right local accelerator: ``mlx`` on macOS (Apple Silicon MPS +
MLX), ``vllm`` on Linux (CUDA), ``lmdeploy`` on Windows. Plain
``pip install mineru`` gives only the CLI client and falls back to a slow
CPU Transformers path for the VLM/hybrid backends.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from .base import BaseParser


MINERU_BACKEND_FLAG_MAP: dict[str, str | None] = {
    # ``auto`` passes no ``-b`` flag, so the mineru CLI picks its current
    # default (``hybrid-auto-engine`` as of mineru 2.x). This preserves the
    # historical behavior of this parser.
    "auto": None,
    "pipeline": "pipeline",
    "vlm": "vlm-auto-engine",
    "hybrid": "hybrid-auto-engine",
}


class MineruParser(BaseParser):
    """Convert PDF to Markdown using the ``mineru`` CLI."""

    name = "mineru"

    def __init__(self, backend: str | None = None, timeout_seconds: int = 900) -> None:
        env_backend = os.environ.get("REVISICA_MINERU_BACKEND")
        resolved_backend = backend or env_backend or "auto"
        if resolved_backend not in MINERU_BACKEND_FLAG_MAP:
            raise ValueError(
                f"Unknown MinerU backend '{resolved_backend}'. "
                f"Expected one of: {sorted(MINERU_BACKEND_FLAG_MAP)}"
            )
        self.backend = resolved_backend
        self.timeout_seconds = timeout_seconds

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
                "  pip install 'mineru[all]'"
            )

        with tempfile.TemporaryDirectory(prefix="revisica_mineru_") as tmp_dir:
            command = [mineru_bin, "-p", str(path), "-o", tmp_dir]
            backend_flag = MINERU_BACKEND_FLAG_MAP[self.backend]
            if backend_flag is not None:
                command += ["-b", backend_flag]

            completed = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=False,
                timeout=self.timeout_seconds,
            )

            if completed.returncode != 0:
                raise RuntimeError(
                    f"mineru failed (exit={completed.returncode}, "
                    f"backend={self.backend}): {completed.stderr}"
                )

            # MinerU writes <stem>/<stem>.md inside the output dir
            for md_file in sorted(Path(tmp_dir).rglob("*.md")):
                content = md_file.read_text(encoding="utf-8")
                if content.strip():
                    return content

            raise RuntimeError(
                f"MinerU produced no Markdown output in {tmp_dir} "
                f"(backend={self.backend})"
            )
