"""Tests for MinerU's image capture pipeline.

Three layers we need to lock in:

  1. ``_run_mineru`` reads images out of the mineru temp directory
     *before* the temp directory is destroyed, keyed by the relative
     path used in the markdown's ``![](images/<sha>.jpg)`` references.
  2. The chunk cache persists those images alongside the cached
     markdown, and a cache hit reconstructs them by re-scanning the
     cached markdown for image references.
  3. ``parse_with_assets`` returns a sorted, deduplicated list of
     :class:`ParsedImage` so downstream storage gets a stable
     write order.

These behaviours are the difference between "figures land in the
Library reader" and "all figures silently disappear after a parse",
which is precisely the regression the original reader bug came from —
none of it was tested before this file.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest


_CHUNK_PDF_NAME_RE = re.compile(r"_p(\d{4,})-p(\d{4,})\.pdf$")


def _make_fake_mineru_with_images(
    image_bytes_by_chunk: dict[tuple[int, int] | None, dict[str, bytes]],
    call_log: list[dict[str, object]] | None = None,
):
    """Build a ``subprocess.run`` fake that emits both markdown and images.

    Mimics mineru's on-disk layout: ``<out>/<stem>/<stem>.md`` plus a
    sibling ``<out>/<stem>/images/<name>`` for each image. The fake
    references each image from the markdown via ``![](images/<name>)``
    so the production code's "scan markdown for image refs" path is
    exercised exactly as it would be against real mineru output.

    ``image_bytes_by_chunk`` is keyed by ``(start, end)`` page tuple for
    chunked calls and ``None`` for the single-shot path. A missing key
    means "this chunk produces no images", which is also a valid
    real-world case (a chapter with only text).
    """

    def runner(args, *, capture_output, text, check, timeout):
        out_dir = Path(args[args.index("-o") + 1])
        pdf_path = Path(args[args.index("-p") + 1])

        match = _CHUNK_PDF_NAME_RE.search(pdf_path.name)
        chunk_key: tuple[int, int] | None
        if match:
            chunk_key = (int(match.group(1)), int(match.group(2)))
        else:
            chunk_key = None

        if call_log is not None:
            call_log.append({"chunk_key": chunk_key, "pdf_name": pdf_path.name})

        target_dir = out_dir / pdf_path.stem
        target_dir.mkdir(parents=True, exist_ok=True)

        images_for_this_chunk = image_bytes_by_chunk.get(chunk_key, {})
        image_refs = "\n".join(f"![]({rel})" for rel in sorted(images_for_this_chunk))
        marker = f"# chunk {chunk_key}\n\n{image_refs}\nbody\n"
        (target_dir / f"{pdf_path.stem}.md").write_text(marker, encoding="utf-8")

        if images_for_this_chunk:
            images_dir = target_dir / "images"
            images_dir.mkdir(parents=True, exist_ok=True)
            for rel, data in images_for_this_chunk.items():
                # rel is ``images/<name>`` — strip the leading dir to
                # land bytes in the sibling images dir.
                name = rel.split("/", 1)[1]
                (images_dir / name).write_bytes(data)

        return subprocess.CompletedProcess(args=args, returncode=0, stdout="", stderr="")

    return runner


def _fake_extract_pdf_page_range(source, target, start_page, end_page):
    """Touch-a-file stub matching the one in ``test_ingestion.py``."""
    target.write_bytes(b"%PDF-1.4 fake-chunk")


def _patch_mineru_env(monkeypatch, tmp_path, page_count: int):
    """Pin mineru CLI lookup, page count, splitter, and chunk cache root."""
    from revisica.ingestion import mineru_parser as mp

    monkeypatch.setattr(mp.shutil, "which", lambda _name: "/usr/local/bin/mineru")
    monkeypatch.setattr(mp, "_count_pdf_pages", lambda _path: page_count)
    monkeypatch.setattr(mp, "_extract_pdf_page_range", _fake_extract_pdf_page_range)
    monkeypatch.setenv("REVISICA_MINERU_CHUNK_CACHE_DIR", str(tmp_path / "cache"))


class TestRunMineruImageCapture:
    """``_run_mineru`` collects images sitting next to its markdown output."""

    def test_captures_images_referenced_by_markdown(self, monkeypatch, tmp_path):
        from revisica.ingestion import mineru_parser as mp

        _patch_mineru_env(monkeypatch, tmp_path, page_count=20)
        monkeypatch.setattr(
            mp.subprocess,
            "run",
            _make_fake_mineru_with_images({
                None: {"images/aaa.jpg": b"IMAGE-A", "images/bbb.jpg": b"IMAGE-B"},
            }),
        )

        pdf = tmp_path / "paper.pdf"
        pdf.write_bytes(b"%PDF-1.4 fake")
        parser = mp.MineruParser(chunk_pages_threshold=50, chunk_pages_size=30)

        markdown, images = parser._parse_internal(pdf)

        assert "![](images/aaa.jpg)" in markdown
        assert images == {
            "images/aaa.jpg": b"IMAGE-A",
            "images/bbb.jpg": b"IMAGE-B",
        }

    def test_returns_empty_dict_when_pdf_has_no_figures(
        self, monkeypatch, tmp_path,
    ):
        from revisica.ingestion import mineru_parser as mp

        _patch_mineru_env(monkeypatch, tmp_path, page_count=20)
        monkeypatch.setattr(
            mp.subprocess,
            "run",
            _make_fake_mineru_with_images({None: {}}),
        )

        pdf = tmp_path / "paper.pdf"
        pdf.write_bytes(b"%PDF-1.4 fake")
        parser = mp.MineruParser(chunk_pages_threshold=50, chunk_pages_size=30)

        _markdown, images = parser._parse_internal(pdf)
        assert images == {}

    def test_skips_image_refs_whose_file_is_missing(
        self, monkeypatch, tmp_path,
    ):
        """Mineru sometimes references an image that it then drops on disk.

        We want a missing referenced file to silently not appear in the
        result, not to crash the parse.
        """
        from revisica.ingestion import mineru_parser as mp

        _patch_mineru_env(monkeypatch, tmp_path, page_count=20)

        def runner(args, *, capture_output, text, check, timeout):
            out_dir = Path(args[args.index("-o") + 1])
            pdf_path = Path(args[args.index("-p") + 1])
            target_dir = out_dir / pdf_path.stem
            target_dir.mkdir(parents=True, exist_ok=True)
            (target_dir / f"{pdf_path.stem}.md").write_text(
                "![](images/missing.jpg)\n![](images/present.jpg)\n",
                encoding="utf-8",
            )
            images_dir = target_dir / "images"
            images_dir.mkdir(parents=True, exist_ok=True)
            (images_dir / "present.jpg").write_bytes(b"PRESENT")
            # ``missing.jpg`` is deliberately not written.
            return subprocess.CompletedProcess(args=args, returncode=0, stdout="", stderr="")

        monkeypatch.setattr(mp.subprocess, "run", runner)

        pdf = tmp_path / "paper.pdf"
        pdf.write_bytes(b"%PDF-1.4 fake")
        parser = mp.MineruParser(chunk_pages_threshold=50, chunk_pages_size=30)
        _markdown, images = parser._parse_internal(pdf)

        assert images == {"images/present.jpg": b"PRESENT"}

    def test_rejects_traversal_in_image_ref(self, monkeypatch, tmp_path):
        """A ``../`` segment in an image ref must never read outside the dir.

        Defensive guard — mineru shouldn't ever produce such refs, but a
        compromised upstream or a malicious PDF must not be able to slip
        host files into a parse result via the alt-text channel.
        """
        from revisica.ingestion import mineru_parser as mp

        _patch_mineru_env(monkeypatch, tmp_path, page_count=20)
        secret = tmp_path / "secret.txt"
        secret.write_text("must-not-leak")

        def runner(args, *, capture_output, text, check, timeout):
            out_dir = Path(args[args.index("-o") + 1])
            pdf_path = Path(args[args.index("-p") + 1])
            target_dir = out_dir / pdf_path.stem
            target_dir.mkdir(parents=True, exist_ok=True)
            (target_dir / f"{pdf_path.stem}.md").write_text(
                "![](../../secret.txt)\n",
                encoding="utf-8",
            )
            return subprocess.CompletedProcess(args=args, returncode=0, stdout="", stderr="")

        monkeypatch.setattr(mp.subprocess, "run", runner)

        pdf = tmp_path / "paper.pdf"
        pdf.write_bytes(b"%PDF-1.4 fake")
        parser = mp.MineruParser(chunk_pages_threshold=50, chunk_pages_size=30)
        _markdown, images = parser._parse_internal(pdf)
        assert images == {}


class TestChunkCacheImageRoundTrip:
    """Per-chunk images survive a write + cache-hit reconstruction cycle."""

    def test_chunk_writes_images_into_cache_dir(self, monkeypatch, tmp_path):
        """Fresh chunk parse persists images next to the cached markdown."""
        from revisica.ingestion import mineru_parser as mp

        _patch_mineru_env(monkeypatch, tmp_path, page_count=70)
        monkeypatch.setattr(
            mp.subprocess,
            "run",
            _make_fake_mineru_with_images({
                (0, 29): {"images/chunk1.jpg": b"CHUNK1"},
                (30, 59): {"images/chunk2.jpg": b"CHUNK2"},
                (60, 69): {},
            }),
        )

        pdf = tmp_path / "paper.pdf"
        pdf.write_bytes(b"%PDF-1.4 cache-write")

        parser = mp.MineruParser(chunk_pages_threshold=50, chunk_pages_size=30)
        _markdown, images = parser._parse_internal(pdf)

        assert images == {
            "images/chunk1.jpg": b"CHUNK1",
            "images/chunk2.jpg": b"CHUNK2",
        }

        # And the images are physically on disk in the cache. Pipeline
        # backend is the fallback default when vlm is requested; under
        # vlm the cache dir is named accordingly.
        pdf_hash = mp._compute_pdf_hash(pdf)
        vlm_cache = mp.chunk_cache_dir_for(pdf_hash, "vlm")
        assert (vlm_cache / "images" / "chunk1.jpg").read_bytes() == b"CHUNK1"
        assert (vlm_cache / "images" / "chunk2.jpg").read_bytes() == b"CHUNK2"

    def test_cache_hit_reconstructs_images_from_disk(
        self, monkeypatch, tmp_path,
    ):
        """Re-parse with no subprocess calls reads images from cache."""
        from revisica.ingestion import mineru_parser as mp

        _patch_mineru_env(monkeypatch, tmp_path, page_count=70)
        monkeypatch.setattr(
            mp.subprocess,
            "run",
            _make_fake_mineru_with_images({
                (0, 29): {"images/chunk1.jpg": b"CHUNK1"},
                (30, 59): {"images/chunk2.jpg": b"CHUNK2"},
                (60, 69): {},
            }),
        )

        pdf = tmp_path / "paper.pdf"
        pdf.write_bytes(b"%PDF-1.4 cache-hit")
        parser = mp.MineruParser(chunk_pages_threshold=50, chunk_pages_size=30)
        parser._parse_internal(pdf)  # warm cache

        # Now make the subprocess fake explode if called — every chunk
        # must come from cache on this second pass.
        def explode(*_a, **_kw):
            raise AssertionError("subprocess.run must not be called on cache hit")
        monkeypatch.setattr(mp.subprocess, "run", explode)

        _markdown, images = parser._parse_internal(pdf)
        assert images == {
            "images/chunk1.jpg": b"CHUNK1",
            "images/chunk2.jpg": b"CHUNK2",
        }

    def test_legacy_cache_without_images_dir_returns_empty(
        self, monkeypatch, tmp_path,
    ):
        """A cache written before image support returns an empty image dict.

        We can't recover images that were never persisted, but the parse
        must still succeed — that's how the migration path works for
        users with thousands of pre-existing cached chunks.
        """
        from revisica.ingestion import mineru_parser as mp

        _patch_mineru_env(monkeypatch, tmp_path, page_count=70)

        # Seed the cache with markdown only, no images dir — mimicking a
        # parse that ran under the old code path.
        pdf = tmp_path / "paper.pdf"
        pdf.write_bytes(b"%PDF-1.4 legacy-cache")
        pdf_hash = mp._compute_pdf_hash(pdf)
        for start, end in [(0, 29), (30, 59), (60, 69)]:
            cache_dir = mp.chunk_cache_dir_for(pdf_hash, "vlm")
            cache_dir.mkdir(parents=True, exist_ok=True)
            (cache_dir / f"p{start:04d}-p{end:04d}.md").write_text(
                f"# legacy chunk {start}-{end}\n\n![](images/orphan.jpg)\nbody\n",
                encoding="utf-8",
            )

        def explode(*_a, **_kw):
            raise AssertionError("subprocess.run must not be called on cache hit")
        monkeypatch.setattr(mp.subprocess, "run", explode)

        parser = mp.MineruParser(chunk_pages_threshold=50, chunk_pages_size=30)
        markdown, images = parser._parse_internal(pdf)
        assert "legacy chunk 0-29" in markdown
        assert images == {}  # The ``![](images/orphan.jpg)`` ref has no file behind it.


class TestParseWithAssets:
    """The public ``parse_with_assets`` adapter on the parser instance."""

    def test_returns_sorted_parsed_image_list(self, monkeypatch, tmp_path):
        """A stable sort order means storage's on-disk write order is stable too.

        Without it, two consecutive ``save_parsed_document`` calls on the
        same parse could shuffle file mtimes, which makes ``ls -t``
        debugging confusing and breaks any future content hash on the
        full asset directory.
        """
        from revisica.ingestion import mineru_parser as mp
        from revisica.ingestion.types import ParsedImage

        _patch_mineru_env(monkeypatch, tmp_path, page_count=20)
        monkeypatch.setattr(
            mp.subprocess,
            "run",
            _make_fake_mineru_with_images({
                None: {
                    "images/zzz.jpg": b"Z",
                    "images/aaa.jpg": b"A",
                    "images/mmm.jpg": b"M",
                },
            }),
        )

        pdf = tmp_path / "paper.pdf"
        pdf.write_bytes(b"%PDF-1.4 fake")
        parser = mp.MineruParser(chunk_pages_threshold=50, chunk_pages_size=30)

        _markdown, images = parser.parse_with_assets(pdf)
        assert all(isinstance(img, ParsedImage) for img in images)
        assert [img.relative_path for img in images] == [
            "images/aaa.jpg", "images/mmm.jpg", "images/zzz.jpg",
        ]
        assert [img.data for img in images] == [b"A", b"M", b"Z"]

    def test_dedupes_images_across_chunks(self, monkeypatch, tmp_path):
        """Mineru's image filenames are content-addressed sha256 hashes.

        Two chunks referencing the same figure produce the same filename
        and the same bytes, so the merged dict semantics naturally
        deduplicate them. We assert the dedupe explicitly so a future
        refactor that switched to list concatenation (and produced
        duplicate ParsedImage entries) would fail this test.
        """
        from revisica.ingestion import mineru_parser as mp

        _patch_mineru_env(monkeypatch, tmp_path, page_count=70)
        monkeypatch.setattr(
            mp.subprocess,
            "run",
            _make_fake_mineru_with_images({
                (0, 29): {"images/shared.jpg": b"SAME"},
                (30, 59): {"images/shared.jpg": b"SAME"},
                (60, 69): {},
            }),
        )

        pdf = tmp_path / "paper.pdf"
        pdf.write_bytes(b"%PDF-1.4 dedupe")
        parser = mp.MineruParser(chunk_pages_threshold=50, chunk_pages_size=30)
        _markdown, images = parser.parse_with_assets(pdf)

        relative_paths = [img.relative_path for img in images]
        assert relative_paths == ["images/shared.jpg"]
