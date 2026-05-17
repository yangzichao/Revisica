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
attempt. Cache layout per backend:
``<pdf_hash>/<backend>/p####-p####.md`` for the chunk's markdown plus
``<pdf_hash>/<backend>/images/<sha>.jpg`` for any figures mineru
extracted from those pages (the image filenames are content-addressed
sha256 hashes from mineru, so the flat shared ``images/`` dir never
collides across chunks). Cache hits reconstruct ``(md, images)`` by
re-scanning the cached markdown for ``![](images/<sha>.jpg)``
references — older caches that predate image capture simply find no
matching files and return an empty image dict, which is correct.

When the requested backend is ``vlm`` and a single chunk crashes
(notably the mlx_vlm BPE detokenizer's recurring 0xb0
``UnicodeDecodeError`` on certain image-heavy pages), we automatically
re-run just that chunk through the ``pipeline`` backend. The successful
fallback markdown is cached under ``<pdf_hash>/pipeline/`` so subsequent
retries hit it without re-running pipeline. Disable with
``REVISICA_MINERU_CHUNK_FALLBACK_BACKEND=none``.
"""

from __future__ import annotations

import dataclasses
import hashlib
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Callable

from .base import BaseParser
from .types import ParsedImage


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
CHUNK_FALLBACK_BACKEND_ENV_VAR = "REVISICA_MINERU_CHUNK_FALLBACK_BACKEND"


@dataclasses.dataclass(frozen=True)
class MineruChunkProgress:
    """Reported once per chunk transition so the UI can render a progress bar.

    ``status`` is one of:
      - ``"running"``   : MinerU was just spawned for this chunk
      - ``"completed"`` : chunk finished and was written to the cache
      - ``"cached"``    : chunk was already in the cache and was skipped
      - ``"fallback"``  : primary backend raised; retrying this chunk
                          with the fallback backend (typically vlm → pipeline
                          on the books that trip mlx_vlm's BPE detokenizer)
      - ``"failed"``    : MinerU raised on this chunk under every backend
                          we tried; the parse aborts

    ``backend`` is the mineru backend used for the *last* run of this chunk
    (``None`` for cached events from before this field existed). It exists
    so the UI can flag "this chunk fell back to pipeline" without having
    to infer it from the status transition.
    """

    chunk_index: int  # 1-based
    chunk_total: int
    start_page: int  # 0-based, inclusive
    end_page: int  # 0-based, inclusive
    status: str
    backend: str | None = None


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
        markdown, _ = self._parse_internal(path)
        return markdown

    def parse_with_assets(self, path: Path) -> tuple[str, list[ParsedImage]]:
        markdown, images = self._parse_internal(path)
        return markdown, [
            ParsedImage(relative_path=rel, data=data)
            for rel, data in sorted(images.items())
        ]

    def _parse_internal(self, path: Path) -> tuple[str, dict[str, bytes]]:
        """Run mineru and return (markdown, image_bytes_by_relative_path).

        Images are keyed by the path used in the markdown's ``![](...)``
        references (mineru emits ``images/<sha>.jpg``). The dict can be
        empty when the input PDF has no figures or all of them were
        dropped during OCR.
        """
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
    ) -> tuple[str, dict[str, bytes]]:
        """Run the chunked parse with per-chunk backend fallback.

        Cache layout: ``<root>/<pdf_hash>/<backend>/p####-p####.md``. We
        check the primary backend's cache first; on miss we also peek at
        the fallback backend's cache (a previous attempt may have fallen
        back to pipeline for this chunk and that result is still
        usable). Successful chunks are written under the directory of
        whichever backend actually produced them, so the user can later
        clear just the pipeline-fallback chunks by removing
        ``<pdf_hash>/pipeline/`` if they want to re-attempt them with a
        fixed vlm.

        Empirically: mlx_vlm's BPE detokenizer crashes on certain page
        content (the recurring 0xb0 ``UnicodeDecodeError`` on DDIA's
        chunk 2) and the pipeline backend handles the same content
        cleanly. Per-chunk fallback turns "this book fails forever" into
        "this book takes longer because one chunk routes through
        pipeline".
        """
        pdf_hash = _compute_pdf_hash(path)
        primary_backend = self.backend
        fallback_backend = self._chunk_fallback_backend()

        primary_cache_dir = chunk_cache_dir_for(pdf_hash, primary_backend)
        primary_cache_dir.mkdir(parents=True, exist_ok=True)
        fallback_cache_dir = (
            chunk_cache_dir_for(pdf_hash, fallback_backend)
            if fallback_backend is not None else None
        )

        total = len(chunks)
        pieces: list[str] = []
        merged_images: dict[str, bytes] = {}
        for index, (start, end) in enumerate(chunks, start=1):
            filename = _chunk_filename(start, end)
            primary_cache_path = primary_cache_dir / filename
            fallback_cache_path = (
                fallback_cache_dir / filename
                if fallback_cache_dir is not None else None
            )

            # Cache lookup: primary first, then fallback.
            cached_hit = self._lookup_cached_chunk(
                primary_cache_path, primary_backend,
                fallback_cache_path, fallback_backend,
            )
            if cached_hit is not None:
                chunk_md, chunk_images, cached_from_backend = cached_hit
                self._report(MineruChunkProgress(
                    chunk_index=index, chunk_total=total,
                    start_page=start, end_page=end,
                    status="cached",
                    backend=cached_from_backend,
                ))
                pieces.append(chunk_md)
                merged_images.update(chunk_images)
                continue

            # Run with primary backend.
            self._report(MineruChunkProgress(
                chunk_index=index, chunk_total=total,
                start_page=start, end_page=end,
                status="running",
                backend=primary_backend,
            ))
            try:
                chunk_md, chunk_images = self._run_chunk(
                    path, start, end, primary_backend,
                )
                _atomic_write(primary_cache_path, chunk_md)
                _persist_chunk_images(primary_cache_dir, chunk_images)
                pieces.append(chunk_md)
                merged_images.update(chunk_images)
                self._report(MineruChunkProgress(
                    chunk_index=index, chunk_total=total,
                    start_page=start, end_page=end,
                    status="completed",
                    backend=primary_backend,
                ))
                continue
            except Exception as primary_exc:
                if fallback_backend is None or fallback_cache_path is None:
                    self._report(MineruChunkProgress(
                        chunk_index=index, chunk_total=total,
                        start_page=start, end_page=end,
                        status="failed",
                        backend=primary_backend,
                    ))
                    raise

            # Primary failed and a fallback is configured. Try once more
            # with the fallback backend. If THAT also fails, surface the
            # fallback's error (callers care about the most recent attempt;
            # the primary error message is preserved in the chained
            # ``__context__`` for diagnostics).
            self._report(MineruChunkProgress(
                chunk_index=index, chunk_total=total,
                start_page=start, end_page=end,
                status="fallback",
                backend=fallback_backend,
            ))
            try:
                chunk_md, chunk_images = self._run_chunk(
                    path, start, end, fallback_backend,
                )
            except Exception:
                self._report(MineruChunkProgress(
                    chunk_index=index, chunk_total=total,
                    start_page=start, end_page=end,
                    status="failed",
                    backend=fallback_backend,
                ))
                raise

            _atomic_write(fallback_cache_path, chunk_md)
            assert fallback_cache_dir is not None  # narrowed by guard above
            _persist_chunk_images(fallback_cache_dir, chunk_images)
            pieces.append(chunk_md)
            merged_images.update(chunk_images)
            self._report(MineruChunkProgress(
                chunk_index=index, chunk_total=total,
                start_page=start, end_page=end,
                status="completed",
                backend=fallback_backend,
            ))

        return "\n\n".join(pieces), merged_images

    @staticmethod
    def _lookup_cached_chunk(
        primary_path: Path,
        primary_backend: str,
        fallback_path: Path | None,
        fallback_backend: str | None,
    ) -> tuple[str, dict[str, bytes], str] | None:
        """Return ``(markdown, images, backend_that_produced_it)`` or ``None``.

        Primary cache wins ties; the fallback cache is consulted only
        when the primary cache misses, so we never silently downgrade a
        chunk that was previously parsed under the requested backend.

        Images are looked up next to the cached markdown — see
        :func:`_load_chunk_images_for_markdown`. Older caches written
        before image capture existed simply produce an empty image dict,
        which is correct (the underlying figure files are gone).
        """
        if primary_path.exists():
            markdown = primary_path.read_text(encoding="utf-8")
            images = _load_chunk_images_for_markdown(primary_path.parent, markdown)
            return markdown, images, primary_backend
        if (
            fallback_path is not None
            and fallback_backend is not None
            and fallback_path.exists()
        ):
            markdown = fallback_path.read_text(encoding="utf-8")
            images = _load_chunk_images_for_markdown(fallback_path.parent, markdown)
            return markdown, images, fallback_backend
        return None

    def _chunk_fallback_backend(self) -> str | None:
        """Backend to retry a failed chunk under, or ``None`` to disable.

        The chunk-level vlm → pipeline fallback exists specifically for
        mlx_vlm's BPE detokenizer bug. If the user is already on the
        pipeline backend (or has opted out via env var) there is nothing
        to fall back to.
        """
        override = os.environ.get(CHUNK_FALLBACK_BACKEND_ENV_VAR, "").strip()
        if override == "":
            # Default: only fall back when the primary is NOT pipeline.
            return "pipeline" if self.backend != "pipeline" else None
        if override.lower() in ("none", "disabled", "off"):
            return None
        if override not in MINERU_BACKEND_FLAG_MAP:
            # An invalid override is a user-config bug; surface it
            # rather than silently ignoring it.
            raise ValueError(
                f"{CHUNK_FALLBACK_BACKEND_ENV_VAR}={override!r} is not a "
                f"recognized mineru backend "
                f"(expected one of {sorted(MINERU_BACKEND_FLAG_MAP)} or "
                f"'none'/'disabled'/'off')"
            )
        if override == self.backend:
            # Falling back to the same backend would just re-run the
            # same failure; treat as disabled.
            return None
        return override

    def _run_chunk(
        self,
        source_pdf: Path,
        start_page: int,
        end_page: int,
        backend: str,
    ) -> tuple[str, dict[str, bytes]]:
        """Materialize one chunk as a temp PDF and run mineru on it."""
        with tempfile.TemporaryDirectory(prefix="revisica_chunk_") as tmp_dir:
            chunk_pdf = Path(tmp_dir) / _chunk_pdf_filename(
                source_pdf.stem, start_page, end_page,
            )
            _extract_pdf_page_range(source_pdf, chunk_pdf, start_page, end_page)
            return self._run_mineru(chunk_pdf, backend_override=backend)

    def _run_mineru(
        self,
        path: Path,
        backend_override: str | None = None,
    ) -> tuple[str, dict[str, bytes]]:
        """Invoke the mineru CLI on ``path`` and return ``(markdown, images)``.

        ``path`` is always a standalone PDF — either the user's original
        file (small enough to skip chunking) or one of the per-chunk
        temporary PDFs produced by ``_extract_pdf_page_range``.

        ``backend_override`` lets ``_parse_chunked`` retry a single chunk
        under a different backend (vlm → pipeline) without mutating
        ``self.backend``, which the rest of the parse still treats as
        the user-requested default.

        Images are captured eagerly before the mineru temp directory is
        torn down (mineru writes them as ``<stem>/<backend>/images/<sha>.jpg``
        next to the markdown). They are keyed by the path used in the
        markdown's ``![](...)`` references, so the renderer can resolve
        them later without any path rewriting.
        """
        mineru_bin = shutil.which("mineru")
        # ``parse`` already verified mineru is on PATH; assert here keeps the
        # type narrow for static checkers.
        assert mineru_bin is not None

        backend = backend_override if backend_override is not None else self.backend

        with tempfile.TemporaryDirectory(prefix="revisica_mineru_") as tmp_dir:
            command = [mineru_bin, "-p", str(path), "-o", tmp_dir]
            backend_flag = MINERU_BACKEND_FLAG_MAP[backend]
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
                    f"backend={backend}, input={path.name}): "
                    f"{completed.stderr}"
                )

            for md_file in sorted(Path(tmp_dir).rglob("*.md")):
                content = md_file.read_text(encoding="utf-8")
                if content.strip():
                    images = _collect_images_next_to(md_file)
                    return content, images

            raise RuntimeError(
                f"MinerU produced no Markdown output in {tmp_dir} "
                f"(backend={backend}, input={path.name})"
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


def _atomic_write_bytes(path: Path, data: bytes) -> None:
    """Binary counterpart to :func:`_atomic_write`."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_bytes(data)
    os.replace(tmp_path, path)


# ``![alt](images/<sha>.jpg)`` — mineru emits image references in this
# exact form. We match the entire ``(...)`` group so callers can
# distinguish ``images/foo.jpg`` from ``https://example.com/foo.jpg``
# without false positives on hyperlinks.
_IMAGE_REF_RE = re.compile(r"!\[[^\]]*\]\(([^)\s]+)")


def _collect_images_next_to(markdown_file: Path) -> dict[str, bytes]:
    """Read every image referenced by ``markdown_file`` into memory.

    Mineru places images in ``<markdown_dir>/images/<sha>.jpg``, and the
    markdown body references them as ``![](images/<sha>.jpg)``. We scan
    the markdown for those references and load only the ones that exist —
    silently skipping references whose file is missing (mineru
    occasionally emits a reference for a span it then drops). Returns a
    dict keyed by the relative path used in the markdown so callers can
    feed it back into the renderer without rewriting any paths.
    """
    base = markdown_file.parent
    markdown = markdown_file.read_text(encoding="utf-8")
    images: dict[str, bytes] = {}
    for rel in _extract_image_refs(markdown):
        # Reject anything that escapes the markdown directory or uses an
        # absolute path. Defensive — mineru shouldn't emit either, but a
        # malicious upstream could and we don't want to leak host files.
        if rel.startswith(("/", "http://", "https://", "data:")) or ".." in rel.split("/"):
            continue
        candidate = (base / rel).resolve()
        try:
            candidate.relative_to(base.resolve())
        except ValueError:
            continue
        if candidate.is_file():
            images[rel] = candidate.read_bytes()
    return images


def _extract_image_refs(markdown: str) -> list[str]:
    """Return every relative image path referenced by ``markdown``."""
    return _IMAGE_REF_RE.findall(markdown)


def _persist_chunk_images(chunk_cache_dir: Path, images: dict[str, bytes]) -> None:
    """Write per-chunk images into the chunk cache directory.

    Layout: ``<chunk_cache_dir>/<relative_path>`` (typically
    ``<chunk_cache_dir>/images/<sha>.jpg``). We use the same relative
    paths the markdown references so cache hits can reconstruct the
    ``(markdown, images)`` tuple by re-scanning the cached ``.md``.
    """
    for rel, data in images.items():
        target = (chunk_cache_dir / rel).resolve()
        try:
            target.relative_to(chunk_cache_dir.resolve())
        except ValueError:
            # Defense in depth: refuse to write outside the cache dir.
            continue
        _atomic_write_bytes(target, data)


def _load_chunk_images_for_markdown(
    chunk_cache_dir: Path,
    markdown: str,
) -> dict[str, bytes]:
    """Return image bytes for every reference in a cached chunk's markdown.

    Missing files are silently skipped — that's how older caches written
    before image capture existed behave automatically (no images dir, no
    images returned), and matches :func:`_collect_images_next_to`.
    """
    images: dict[str, bytes] = {}
    for rel in _extract_image_refs(markdown):
        if rel.startswith(("/", "http://", "https://", "data:")) or ".." in rel.split("/"):
            continue
        candidate = (chunk_cache_dir / rel).resolve()
        try:
            candidate.relative_to(chunk_cache_dir.resolve())
        except ValueError:
            continue
        if candidate.is_file():
            images[rel] = candidate.read_bytes()
    return images


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
