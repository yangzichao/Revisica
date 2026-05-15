"""PDF -> Markdown parser via MinerU CLI.

Install: ``pip install 'mineru[all]'``. The ``[all]`` extra is platform-aware
and pulls the right local accelerator: ``mlx`` on macOS (Apple Silicon MPS +
MLX), ``vllm`` on Linux (CUDA), ``lmdeploy`` on Windows. Plain
``pip install mineru`` gives only the CLI client and falls back to a slow
CPU Transformers path for the VLM/hybrid backends.

Large PDFs (hundreds of pages) blow out GPU memory when fed to MinerU as a
single job, so this parser auto-splits anything above
``REVISICA_MINERU_CHUNK_THRESHOLD`` pages into chunks of
``REVISICA_MINERU_CHUNK_SIZE`` pages. Each chunk is materialized as a
*physical* temporary PDF via ``pypdfium2`` (PDFium — Chrome's PDF engine,
already a transitive dependency of mineru itself) and fed to mineru as a
standalone file — equivalent to what a user would do manually with a PDF
splitter.

We deliberately do **not** use mineru's native ``-s/--start`` and
``-e/--end`` flags: in practice they leave the full PDF's font tables /
metadata / character encoding loaded around the VLM tokenizer's state,
which on certain books produces ``UnicodeDecodeError`` deep inside
``mlx_vlm`` for page ranges that parse cleanly when split into a real
sub-PDF. Splitting up front matches a manual workflow that empirically
works and isolates each chunk's tokenizer state.

We also deliberately do **not** use ``pypdf.PdfWriter(clone_from=...)``
plus ``del writer.pages[i]``. That approach removes pages from the
``/Pages`` tree but leaves every other indirect object (orphan page
dicts, all source-document fonts, ICC profiles, image XObjects) in the
output. On Designing Data-Intensive Applications a 30-page chunk
extracted that way is 24 MB — the same size as the 613-page source —
versus 2 MB via pypdfium2. mineru's vlm pipeline then trips over those
ghost objects and produces non-UTF-8 token sequences in mlx_vlm's BPE
detokenizer. PDFium does proper resource pruning and produces output
that is byte-equivalent (modulo metadata) to what qpdf / Preview / a
manual splitter would produce.

Each chunk's markdown is content-addressed (``sha256(pdf_bytes)[:16]`` +
backend + page range) so a parse aborted by OOM, cancellation, or a
server restart resumes from the next un-cached chunk on the second
attempt.
"""

from __future__ import annotations

import dataclasses
import hashlib
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Callable

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


DEFAULT_CHUNK_PAGES_THRESHOLD = 50
DEFAULT_CHUNK_PAGES_SIZE = 30

CHUNK_THRESHOLD_ENV_VAR = "REVISICA_MINERU_CHUNK_THRESHOLD"
CHUNK_SIZE_ENV_VAR = "REVISICA_MINERU_CHUNK_SIZE"
CHUNK_CACHE_ROOT_ENV_VAR = "REVISICA_MINERU_CHUNK_CACHE_DIR"


@dataclasses.dataclass(frozen=True)
class MineruChunkProgress:
    """Reported once per chunk transition so the UI can render a progress bar.

    ``status`` is one of:
      - ``"running"``  : MinerU was just spawned for this chunk
      - ``"completed"``: chunk finished and was written to the cache
      - ``"cached"``   : chunk was already in the cache and was skipped
      - ``"failed"``   : MinerU raised on this chunk (the parse aborts)
    """

    chunk_index: int  # 1-based
    chunk_total: int
    start_page: int  # 0-based, inclusive
    end_page: int  # 0-based, inclusive
    status: str


ProgressCallback = Callable[[MineruChunkProgress], None]


class MineruParser(BaseParser):
    """Convert PDF to Markdown using the ``mineru`` CLI."""

    name = "mineru"

    def __init__(
        self,
        backend: str | None = None,
        timeout_seconds: int = 7200,
        chunk_pages_threshold: int | None = None,
        chunk_pages_size: int | None = None,
        progress_callback: ProgressCallback | None = None,
    ) -> None:
        env_backend = os.environ.get("REVISICA_MINERU_BACKEND")
        resolved_backend = backend or env_backend or "vlm"
        if resolved_backend not in MINERU_BACKEND_FLAG_MAP:
            raise ValueError(
                f"Unknown MinerU backend '{resolved_backend}'. "
                f"Expected one of: {sorted(MINERU_BACKEND_FLAG_MAP)}"
            )
        self.backend = resolved_backend
        self.timeout_seconds = timeout_seconds
        self.chunk_pages_threshold = _resolve_int(
            chunk_pages_threshold,
            CHUNK_THRESHOLD_ENV_VAR,
            DEFAULT_CHUNK_PAGES_THRESHOLD,
        )
        self.chunk_pages_size = _resolve_int(
            chunk_pages_size,
            CHUNK_SIZE_ENV_VAR,
            DEFAULT_CHUNK_PAGES_SIZE,
        )
        if self.chunk_pages_size < 1:
            raise ValueError(
                f"chunk_pages_size must be >= 1 (got {self.chunk_pages_size})"
            )
        self.progress_callback = progress_callback

    def can_handle(self, path: Path) -> bool:
        return path.suffix.lower() == ".pdf"

    @classmethod
    def is_available(cls) -> bool:
        return shutil.which("mineru") is not None

    def parse(self, path: Path) -> str:
        if shutil.which("mineru") is None:
            raise RuntimeError(
                "MinerU is not installed. Install with:\n"
                "  pip install 'mineru[all]'"
            )

        try:
            page_count = _count_pdf_pages(path)
        except Exception:
            # pypdf rejects malformed PDF headers; rather than fail the whole
            # parse on a header quirk that mineru itself can usually handle,
            # fall back to the single-shot path. This costs us auto-chunking
            # for that one file, but matches pre-chunking behavior exactly.
            return self._run_mineru(path)

        if page_count <= self.chunk_pages_threshold:
            return self._run_mineru(path)

        chunks = _chunk_ranges(page_count, self.chunk_pages_size)
        return self._parse_chunked(path, chunks)

    def _parse_chunked(
        self,
        path: Path,
        chunks: list[tuple[int, int]],
    ) -> str:
        pdf_hash = _compute_pdf_hash(path)
        cache_dir = chunk_cache_dir_for(pdf_hash, self.backend)
        cache_dir.mkdir(parents=True, exist_ok=True)

        total = len(chunks)
        pieces: list[str] = []
        for index, (start, end) in enumerate(chunks, start=1):
            cache_path = cache_dir / _chunk_filename(start, end)
            if cache_path.exists():
                self._report(MineruChunkProgress(
                    chunk_index=index,
                    chunk_total=total,
                    start_page=start,
                    end_page=end,
                    status="cached",
                ))
                pieces.append(cache_path.read_text(encoding="utf-8"))
                continue

            self._report(MineruChunkProgress(
                chunk_index=index,
                chunk_total=total,
                start_page=start,
                end_page=end,
                status="running",
            ))
            try:
                # Materialize this chunk as a standalone temporary PDF and
                # feed it to mineru — see module docstring for why this is
                # safer than ``mineru -s/-e``.
                with tempfile.TemporaryDirectory(prefix="revisica_chunk_") as tmp_dir:
                    chunk_pdf = Path(tmp_dir) / _chunk_pdf_filename(
                        path.stem, start, end,
                    )
                    _extract_pdf_page_range(path, chunk_pdf, start, end)
                    chunk_md = self._run_mineru(chunk_pdf)
            except Exception:
                # Tell the UI which chunk specifically blew up so the
                # progress page does not leave a chunk stuck on "running"
                # next to a top-level "parse: failed".
                self._report(MineruChunkProgress(
                    chunk_index=index,
                    chunk_total=total,
                    start_page=start,
                    end_page=end,
                    status="failed",
                ))
                raise
            _atomic_write(cache_path, chunk_md)
            pieces.append(chunk_md)
            self._report(MineruChunkProgress(
                chunk_index=index,
                chunk_total=total,
                start_page=start,
                end_page=end,
                status="completed",
            ))

        return "\n\n".join(pieces)

    def _run_mineru(self, path: Path) -> str:
        """Invoke the mineru CLI on ``path`` and return its markdown output.

        ``path`` is always a standalone PDF — either the user's original
        file (small enough to skip chunking) or one of the per-chunk
        temporary PDFs produced by ``_extract_pdf_page_range``.
        """
        mineru_bin = shutil.which("mineru")
        # ``parse`` already verified mineru is on PATH; assert here keeps the
        # type narrow for static checkers.
        assert mineru_bin is not None

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
                    f"backend={self.backend}, input={path.name}): "
                    f"{completed.stderr}"
                )

            for md_file in sorted(Path(tmp_dir).rglob("*.md")):
                content = md_file.read_text(encoding="utf-8")
                if content.strip():
                    return content

            raise RuntimeError(
                f"MinerU produced no Markdown output in {tmp_dir} "
                f"(backend={self.backend}, input={path.name})"
            )

    def _report(self, progress: MineruChunkProgress) -> None:
        if self.progress_callback is None:
            return
        try:
            self.progress_callback(progress)
        except Exception:
            # A buggy progress callback must not abort the parse — chunk
            # work has already happened (or is about to) and the caller
            # cares about the markdown, not the progress bar.
            pass


# ── helpers ──────────────────────────────────────────────────────────


def _resolve_int(explicit: int | None, env_var: str, default: int) -> int:
    if explicit is not None:
        return explicit
    raw = os.environ.get(env_var, "").strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _count_pdf_pages(path: Path) -> int:
    """Read just enough of the PDF to count pages; pure Python, no GPU."""
    from pypdf import PdfReader

    reader = PdfReader(str(path))
    return len(reader.pages)


def _extract_pdf_page_range(
    source: Path,
    target: Path,
    start_page: int,
    end_page: int,
) -> None:
    """Write pages ``[start_page, end_page]`` of ``source`` to ``target``.

    Both bounds are 0-based and inclusive (so ``(0, 29)`` writes 30 pages).

    Implementation: ``pypdfium2.PdfDocument.import_pages``. PDFium walks
    the page resource graph and copies only the indirect objects that
    the imported pages actually reference, then writes a fresh
    cross-reference table. The output is the smallest valid PDF that
    renders those pages — typically tens to hundreds of times smaller
    than the source on a large book.

    See the module docstring for why neither ``mineru -s/-e``, nor a
    ``pypdf.add_page`` loop, nor ``pypdf.PdfWriter(clone_from=) + del``
    works here. The short version: every alternative we tried either
    drops inherited resources (broken rendering) or retains the entire
    source document's object graph (mlx_vlm BPE detokenizer trips on
    ghost objects). PDFium does the structurally correct thing.

    We close both documents explicitly. ``pypdfium2`` is a thin
    ctypes wrapper around PDFium and holds native memory until
    finalized; relying on ``__del__`` works for short-lived scripts but
    not inside a long-running parse worker that processes hundreds of
    chunks across many books.
    """
    import pypdfium2 as pdfium

    src = pdfium.PdfDocument(str(source))
    try:
        source_page_count = len(src)
        if start_page < 0:
            raise ValueError(f"start_page must be >= 0 (got {start_page})")
        if start_page >= source_page_count:
            raise ValueError(
                f"start_page {start_page} is past source EOF "
                f"({source_page_count} pages)"
            )
        last_index = min(end_page, source_page_count - 1)
        if last_index < start_page:
            raise ValueError(
                f"page range [{start_page}, {end_page}] is empty "
                f"(clamped end {last_index} < start)"
            )

        page_indices = list(range(start_page, last_index + 1))
        # Defense in depth: ``pypdfium2.PdfDocument.import_pages`` treats a
        # falsy ``pages`` argument as "import every page", which would
        # silently turn a buggy range into a full-document copy. The
        # guards above already prevent that, but assert here so a future
        # refactor cannot regress the invariant.
        assert page_indices, "internal invariant: page_indices must be non-empty"

        dst = pdfium.PdfDocument.new()
        try:
            dst.import_pages(src, pages=page_indices)
            dst.save(str(target))
        finally:
            dst.close()
    finally:
        src.close()


def _chunk_pdf_filename(source_stem: str, start: int, end: int) -> str:
    """Produce a stable filename for a per-chunk temporary PDF.

    The page range is in the stem so log lines and mineru-internal
    diagnostics make it obvious which slice the worker is currently on.
    """
    safe_stem = source_stem.strip() or "document"
    return f"{safe_stem}_p{start:04d}-p{end:04d}.pdf"


def _chunk_ranges(total_pages: int, chunk_size: int) -> list[tuple[int, int]]:
    """Split ``total_pages`` into inclusive 0-based ``(start, end)`` ranges."""
    ranges: list[tuple[int, int]] = []
    cursor = 0
    while cursor < total_pages:
        end = min(cursor + chunk_size - 1, total_pages - 1)
        ranges.append((cursor, end))
        cursor = end + 1
    return ranges


def _compute_pdf_hash(path: Path) -> str:
    """Return ``sha256(pdf_bytes)[:16]`` for stable content-addressed cache keys."""
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        while True:
            chunk = fh.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()[:16]


def chunk_cache_root() -> Path:
    """Root directory for chunk-level MinerU caches.

    Honors ``REVISICA_MINERU_CHUNK_CACHE_DIR`` first; otherwise lives under
    ``$XDG_CACHE_HOME`` (or ``~/.cache``).
    """
    override = os.environ.get(CHUNK_CACHE_ROOT_ENV_VAR, "").strip()
    if override:
        return Path(override).expanduser()
    xdg = os.environ.get("XDG_CACHE_HOME", "").strip()
    base = Path(xdg).expanduser() if xdg else Path.home() / ".cache"
    return base / "revisica" / "mineru_chunks"


def chunk_cache_dir_for(pdf_hash: str, backend: str) -> Path:
    return chunk_cache_root() / pdf_hash / backend


def _chunk_filename(start: int, end: int) -> str:
    return f"p{start:04d}-p{end:04d}.md"


def _atomic_write(path: Path, content: str) -> None:
    """Write ``content`` to ``path`` via a sibling tempfile + rename.

    A half-completed chunk file would poison the cache forever, so we never
    expose the partial write to readers — rename is atomic on the same
    filesystem, which is always true for tempfile-in-target-dir.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(content, encoding="utf-8")
    os.replace(tmp_path, path)


def clear_chunk_cache() -> int:
    """Remove every cached chunk. Returns the number of chunk files deleted."""
    root = chunk_cache_root()
    if not root.exists():
        return 0
    removed = sum(1 for _ in root.rglob("*.md"))
    shutil.rmtree(root)
    return removed


__all__ = [
    "MINERU_BACKEND_FLAG_MAP",
    "MineruChunkProgress",
    "MineruParser",
    "ProgressCallback",
    "chunk_cache_dir_for",
    "chunk_cache_root",
    "clear_chunk_cache",
]
