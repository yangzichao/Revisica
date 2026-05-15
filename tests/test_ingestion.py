"""Tests for the ingestion layer: parsers, normalize, and registry."""

from __future__ import annotations

import re
import subprocess
import textwrap
from pathlib import Path

import pytest

from revisica.ingestion.base import BaseParser
from revisica.ingestion.markdown_parser import MarkdownParser
from revisica.ingestion.normalize import (
    normalize_to_document,
    _extract_sections,
    _extract_metadata,
)
from revisica.ingestion.registry import parse_document
from revisica.ingestion.types import RevisicaDocument

FIXTURES = Path(__file__).parent / "fixtures"
SAMPLE_MD = FIXTURES / "sample_paper.md"
SAMPLE_MMD = FIXTURES / "sample_paper.mmd"


# ── MarkdownParser ─────────────────────────────────────────────────────


class TestMarkdownParser:
    def test_is_available(self):
        assert MarkdownParser.is_available() is True

    def test_can_handle_md(self):
        p = MarkdownParser()
        assert p.can_handle(Path("paper.md"))
        assert p.can_handle(Path("paper.mmd"))
        assert p.can_handle(Path("paper.markdown"))
        assert not p.can_handle(Path("paper.tex"))
        assert not p.can_handle(Path("paper.pdf"))

    def test_parse_md(self):
        p = MarkdownParser()
        content = p.parse(SAMPLE_MD)
        assert "# A Very Small Example Paper" in content
        assert r"\int_0^1 x^2" in content
        assert r"\frac{1}{2}" in content

    def test_parse_mmd(self):
        p = MarkdownParser()
        content = p.parse(SAMPLE_MMD)
        assert "# A Very Small Example Paper" in content
        assert "$$" in content

    def test_md_and_mmd_produce_same_output(self):
        p = MarkdownParser()
        md_content = p.parse(SAMPLE_MD)
        mmd_content = p.parse(SAMPLE_MMD)
        assert md_content == mmd_content


# ── normalize_to_document ──────────────────────────────────────────────


class TestNormalize:
    def test_sections_extracted(self):
        md = SAMPLE_MD.read_text(encoding="utf-8")
        sections = _extract_sections(md)
        # Top-level: the H1 title
        assert len(sections) == 1
        root = sections[0]
        assert root.title == "A Very Small Example Paper"
        # Children: the H2 sections
        child_titles = [s.title for s in root.children]
        assert "Introduction" in child_titles
        assert "Main Result" in child_titles
        assert "Conclusion" in child_titles

    def test_metadata_title(self):
        md = SAMPLE_MD.read_text(encoding="utf-8")
        meta = _extract_metadata(md)
        assert meta.title == "A Very Small Example Paper"

    def test_metadata_author(self):
        md = SAMPLE_MD.read_text(encoding="utf-8")
        meta = _extract_metadata(md)
        assert "Revisica Demo" in meta.authors

    def test_normalize_full(self):
        md = SAMPLE_MD.read_text(encoding="utf-8")
        doc = normalize_to_document(md, str(SAMPLE_MD), "markdown")
        assert isinstance(doc, RevisicaDocument)
        assert doc.parser_used == "markdown"
        assert doc.markdown == md
        assert len(doc.sections) > 0
        assert doc.metadata.title == "A Very Small Example Paper"

    def test_empty_markdown(self):
        doc = normalize_to_document("", "empty.md", "markdown")
        assert doc.sections == []
        assert doc.metadata.title == ""

    def test_math_preserved_in_document(self):
        md = SAMPLE_MD.read_text(encoding="utf-8")
        doc = normalize_to_document(md, str(SAMPLE_MD), "markdown")
        assert r"\int_0^1" in doc.markdown
        assert r"\frac{1}{2}" in doc.markdown

    def test_nested_sections(self):
        md = textwrap.dedent("""\
            # Title

            ## Section 1

            Content 1.

            ### Subsection 1.1

            Sub content.

            ## Section 2

            Content 2.
        """)
        doc = normalize_to_document(md, "test.md", "test")
        # Top-level: just "Title"
        assert len(doc.sections) == 1
        root = doc.sections[0]
        assert root.title == "Title"
        # Children: Section 1, Section 2
        assert len(root.children) == 2
        assert root.children[0].title == "Section 1"
        assert root.children[1].title == "Section 2"
        # Sub-children: Subsection 1.1 under Section 1
        assert len(root.children[0].children) == 1
        assert root.children[0].children[0].title == "Subsection 1.1"


# ── registry (parse_document) ─────────────────────────────────────────


class TestRegistry:
    def test_parse_md_auto(self):
        doc = parse_document(SAMPLE_MD)
        assert isinstance(doc, RevisicaDocument)
        assert doc.parser_used == "markdown"

    def test_parse_mmd_auto(self):
        doc = parse_document(SAMPLE_MMD)
        assert isinstance(doc, RevisicaDocument)
        assert doc.parser_used == "markdown"

    def test_parse_md_explicit(self):
        doc = parse_document(SAMPLE_MD, parser="markdown")
        assert doc.parser_used == "markdown"

    def test_parse_nonexistent_file(self):
        with pytest.raises(FileNotFoundError):
            parse_document("/nonexistent/paper.md")

    def test_parse_unsupported_extension(self, tmp_path):
        weird = tmp_path / "paper.xyz"
        weird.write_text("hello")
        with pytest.raises(RuntimeError, match="No parser can handle"):
            parse_document(weird)

    def test_parse_tex_auto(self):
        tex_file = Path(__file__).parent.parent / "examples" / "minimal_paper.tex"
        if not tex_file.exists():
            pytest.skip("examples/minimal_paper.tex not found")
        doc = parse_document(tex_file)
        assert isinstance(doc, RevisicaDocument)
        assert doc.parser_used in ("pandoc", "tex-basic")
        assert len(doc.sections) > 0

    def test_parser_not_available(self):
        with pytest.raises(ValueError, match="not available"):
            parse_document(SAMPLE_MD, parser="nonexistent-parser")


# ── MinerU parser ──────────────────────────────────────────────────────

MINERU_SAMPLE = FIXTURES / "mineru_output_sample.md"


def _fake_mineru_run(args, *, capture_output, text, check, timeout):
    """Simulate ``mineru -p input.pdf -o output_dir``.

    Writes a realistic Markdown file into the output directory using the
    same ``<stem>/<stem>.md`` layout MinerU produces.
    """
    # Parse args: ["mineru", "-p", "<pdf>", "-o", "<outdir>"]
    pdf_path = Path(args[args.index("-p") + 1])
    out_dir = Path(args[args.index("-o") + 1])
    stem = pdf_path.stem

    target_dir = out_dir / stem
    target_dir.mkdir(parents=True, exist_ok=True)
    md_file = target_dir / f"{stem}.md"
    md_file.write_text(MINERU_SAMPLE.read_text(encoding="utf-8"), encoding="utf-8")

    return subprocess.CompletedProcess(args=args, returncode=0, stdout="", stderr="")


class TestMineruParser:
    def test_import(self):
        from revisica.ingestion.mineru_parser import MineruParser
        assert MineruParser.name == "mineru"

    def test_can_handle(self):
        from revisica.ingestion.mineru_parser import MineruParser
        p = MineruParser()
        assert p.can_handle(Path("paper.pdf"))
        assert not p.can_handle(Path("paper.tex"))
        assert not p.can_handle(Path("paper.md"))

    def test_not_available_without_cli(self, monkeypatch):
        from revisica.ingestion import mineru_parser as mp
        monkeypatch.setattr(mp.shutil, "which", lambda name: None)
        assert mp.MineruParser.is_available() is False

    def test_parse_mock(self, monkeypatch, tmp_path):
        """Full parse chain with mocked mineru CLI."""
        from revisica.ingestion import mineru_parser as mp

        monkeypatch.setattr(mp.shutil, "which", lambda name: "/usr/local/bin/mineru")
        monkeypatch.setattr(mp.subprocess, "run", _fake_mineru_run)

        fake_pdf = tmp_path / "paper.pdf"
        fake_pdf.write_bytes(b"%PDF-1.4 fake")

        p = mp.MineruParser()
        md = p.parse(fake_pdf)

        # Verify math is preserved
        assert "$$" in md
        assert r"\lambda" in md
        assert r"\frac{t_i}{p_i}" in md
        assert r"\epsilon_{ii}" in md
        assert r"\bar{\theta}" in md
        assert r"\bar{R}" in md

        # Verify structure
        assert "# Optimal Taxation" in md
        assert "## 1 Introduction" in md
        assert "## 3 Main Results" in md
        assert "**Theorem 1**" in md
        assert "**Proposition 2.**" in md

        # Verify table
        assert "Elasticity" in md
        assert "Electronics" in md

    def test_parse_produces_valid_document(self, monkeypatch, tmp_path):
        """MinerU output normalizes into a well-formed RevisicaDocument."""
        from revisica.ingestion import mineru_parser as mp

        monkeypatch.setattr(mp.shutil, "which", lambda name: "/usr/local/bin/mineru")
        monkeypatch.setattr(mp.subprocess, "run", _fake_mineru_run)

        fake_pdf = tmp_path / "taxation.pdf"
        fake_pdf.write_bytes(b"%PDF-1.4 fake")

        p = mp.MineruParser()
        md = p.parse(fake_pdf)
        doc = normalize_to_document(md, str(fake_pdf), "mineru")

        assert isinstance(doc, RevisicaDocument)
        assert doc.parser_used == "mineru"
        assert doc.metadata.title == "Optimal Taxation Under Behavioral Uncertainty"
        assert len(doc.sections) == 1  # top-level H1
        child_titles = [s.title for s in doc.sections[0].children]
        assert "Abstract" in child_titles
        assert "3 Main Results" in child_titles
        assert "5 Conclusion" in child_titles

    def test_parse_cli_failure(self, monkeypatch, tmp_path):
        """RuntimeError when mineru CLI exits non-zero."""
        from revisica.ingestion import mineru_parser as mp

        monkeypatch.setattr(mp.shutil, "which", lambda name: "/usr/local/bin/mineru")
        monkeypatch.setattr(
            mp.subprocess, "run",
            lambda *a, **kw: subprocess.CompletedProcess(
                args=a[0], returncode=1, stdout="", stderr="CUDA out of memory"
            ),
        )

        fake_pdf = tmp_path / "paper.pdf"
        fake_pdf.write_bytes(b"%PDF-1.4 fake")

        p = mp.MineruParser()
        with pytest.raises(RuntimeError, match="CUDA out of memory"):
            p.parse(fake_pdf)

    def test_parse_empty_output(self, monkeypatch, tmp_path):
        """RuntimeError when mineru produces no markdown."""
        from revisica.ingestion import mineru_parser as mp

        monkeypatch.setattr(mp.shutil, "which", lambda name: "/usr/local/bin/mineru")
        monkeypatch.setattr(
            mp.subprocess, "run",
            lambda *a, **kw: subprocess.CompletedProcess(
                args=a[0], returncode=0, stdout="", stderr=""
            ),
        )

        fake_pdf = tmp_path / "paper.pdf"
        fake_pdf.write_bytes(b"%PDF-1.4 fake")

        p = mp.MineruParser()
        with pytest.raises(RuntimeError, match="no Markdown output"):
            p.parse(fake_pdf)


# ── Mathpix parser (import only, no API calls) ────────────────────────


class TestMathpixParser:
    def test_import(self):
        from revisica.ingestion.mathpix_parser import MathpixParser
        assert MathpixParser.name == "mathpix"

    def test_can_handle(self):
        from revisica.ingestion.mathpix_parser import MathpixParser
        p = MathpixParser()
        assert p.can_handle(Path("paper.pdf"))
        assert p.can_handle(Path("figure.png"))
        assert p.can_handle(Path("scan.jpg"))
        assert not p.can_handle(Path("paper.tex"))
        assert not p.can_handle(Path("paper.md"))

    def test_not_available_without_env(self, monkeypatch):
        monkeypatch.delenv("MATHPIX_APP_ID", raising=False)
        monkeypatch.delenv("MATHPIX_APP_KEY", raising=False)
        from revisica.ingestion.mathpix_parser import MathpixParser
        assert MathpixParser.is_available() is False


# ── Pandoc parser fallback to pypandoc-binary ─────────────────────────
#
# When the DMG is installed on a machine with no Homebrew pandoc, the
# parser must still find the pandoc binary that ships inside PyInstaller
# via `pypandoc-binary`. These tests exercise the fallback without
# depending on pandoc actually being on PATH.


class TestPandocParserFallback:
    def test_is_available_uses_path_when_present(self, monkeypatch):
        from revisica.ingestion import pandoc_parser as pp

        monkeypatch.setattr(pp.shutil, "which", lambda _name: "/opt/homebrew/bin/pandoc")
        assert pp.PandocParser.is_available() is True

    def test_is_available_falls_back_to_pypandoc(self, monkeypatch):
        from revisica.ingestion import pandoc_parser as pp

        monkeypatch.setattr(pp.shutil, "which", lambda _name: None)
        monkeypatch.setattr(pp, "_pypandoc_binary_path", lambda: "/bundled/pandoc")
        assert pp.PandocParser.is_available() is True

    def test_is_available_returns_false_when_neither_present(self, monkeypatch):
        from revisica.ingestion import pandoc_parser as pp

        monkeypatch.setattr(pp.shutil, "which", lambda _name: None)
        monkeypatch.setattr(pp, "_pypandoc_binary_path", lambda: None)
        assert pp.PandocParser.is_available() is False

    def test_pypandoc_helper_swallows_missing_module(self, monkeypatch):
        """If pypandoc is not installed at all, the helper returns None."""
        import builtins

        from revisica.ingestion import pandoc_parser as pp

        real_import = builtins.__import__

        def fake_import(name, *args, **kwargs):
            if name == "pypandoc":
                raise ImportError("no module")
            return real_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", fake_import)
        assert pp._pypandoc_binary_path() is None

    def test_pypandoc_helper_swallows_oserror(self, monkeypatch):
        """`pypandoc.get_pandoc_path` raises OSError when no binary found."""
        from revisica.ingestion import pandoc_parser as pp

        class FakePypandoc:
            @staticmethod
            def get_pandoc_path():
                raise OSError("No pandoc was found")

        import sys
        monkeypatch.setitem(sys.modules, "pypandoc", FakePypandoc)
        assert pp._pypandoc_binary_path() is None


# ── MinerU chunking + resumable cache ──────────────────────────────────


_CHUNK_PDF_NAME_RE = re.compile(r"_p(\d{4,})-p(\d{4,})\.pdf$")


def _make_chunked_fake_mineru(call_log: list[dict[str, object]]):
    """Build a ``subprocess.run`` fake that records the chunk slice and
    writes a deterministic chunk-marker markdown file into the output dir.

    The chunking implementation feeds mineru a *physical* sub-PDF per
    chunk (no ``-s/-e`` flags). The page range is encoded in the temp
    PDF's filename (``<stem>_pNNNN-pMMMM.pdf``) so this fake parses the
    range out of the ``-p`` argument to know which chunk is being
    simulated. A bare PDF (no page-range suffix) — i.e. the unchunked
    single-shot path — is recorded with ``start=None, end=None``.
    """

    def runner(args, *, capture_output, text, check, timeout):
        out_dir = Path(args[args.index("-o") + 1])
        pdf_path = Path(args[args.index("-p") + 1])

        match = _CHUNK_PDF_NAME_RE.search(pdf_path.name)
        if match:
            start: int | None = int(match.group(1))
            end: int | None = int(match.group(2))
        else:
            start = None
            end = None
        call_log.append({"start": start, "end": end, "pdf_name": pdf_path.name})

        target_dir = out_dir / pdf_path.stem
        target_dir.mkdir(parents=True, exist_ok=True)
        marker = f"# chunk pages={start}-{end}\n\nbody for {start}-{end}\n"
        (target_dir / f"{pdf_path.stem}.md").write_text(marker, encoding="utf-8")

        return subprocess.CompletedProcess(args=args, returncode=0, stdout="", stderr="")

    return runner


def _fake_extract_pdf_page_range(source, target, start_page, end_page):
    """Stand-in for the PDFium-backed PDF slicer used in chunking tests.

    Just touches a placeholder file at ``target`` so the chunked code path
    can hand it to the fake mineru runner. The real implementation lives
    in ``mineru_parser._extract_pdf_page_range`` and is exercised
    end-to-end by ``TestExtractPdfPageRange`` plus
    ``revisica benchmark-ingestion``."""
    target.write_bytes(b"%PDF-1.4 fake-chunk")


class TestExtractPdfPageRange:
    """End-to-end PDFium round-trip — uses real pypdfium2, no monkeypatch."""

    def _make_blank_pdf(self, path: Path, num_pages: int) -> None:
        from pypdf import PdfWriter
        writer = PdfWriter()
        for _ in range(num_pages):
            writer.add_blank_page(width=100, height=100)
        with path.open("wb") as fh:
            writer.write(fh)

    def test_extracts_exact_page_range(self, tmp_path):
        from revisica.ingestion.mineru_parser import (
            _count_pdf_pages,
            _extract_pdf_page_range,
        )

        source = tmp_path / "book.pdf"
        target = tmp_path / "chunk.pdf"
        self._make_blank_pdf(source, num_pages=70)

        _extract_pdf_page_range(source, target, start_page=30, end_page=59)
        assert _count_pdf_pages(target) == 30  # inclusive both ends

    def test_extracts_last_partial_chunk(self, tmp_path):
        """A trailing chunk that extends past the document clamps to EOF."""
        from revisica.ingestion.mineru_parser import (
            _count_pdf_pages,
            _extract_pdf_page_range,
        )

        source = tmp_path / "book.pdf"
        target = tmp_path / "chunk.pdf"
        self._make_blank_pdf(source, num_pages=70)

        # Chunk size 30 on a 70-page book gives ranges (0,29), (30,59), (60,69).
        # Last range only has 10 pages even though _chunk_ranges produces
        # (60, 69) — but if a future change ever asked for (60, 99) on this
        # document, we should still write 10 pages instead of crashing on
        # an out-of-range page index.
        _extract_pdf_page_range(source, target, start_page=60, end_page=99)
        assert _count_pdf_pages(target) == 10

    def test_sub_pdf_does_not_carry_orphan_objects_from_source(self, tmp_path):
        """The pypdf ``clone_from`` + ``del writer.pages[i]`` trap.

        That approach removes pages from the ``/Pages`` tree but leaves
        every other indirect object (orphan page dicts, source-document
        fonts, ICC profiles, image XObjects) in the output. On Designing
        Data-Intensive Applications a 30-page chunk extracted that way
        was 24 MB — the same size as the 613-page source — versus 2 MB
        through PDFium. mineru's vlm pipeline then tripped over those
        ghost objects and produced non-UTF-8 token sequences in
        mlx_vlm's BPE detokenizer.

        Embed a deliberately fat ``/MyOrphan`` indirect object in the
        source's catalog (1 MB of zeros, not referenced by any page).
        A correct extractor walks the page resource graph and drops
        that object; a clone-and-delete-pages extractor keeps it and
        the chunk inherits the bloat.
        """
        from pypdf import PdfWriter
        from pypdf.generic import DecodedStreamObject, NameObject
        from revisica.ingestion.mineru_parser import _extract_pdf_page_range

        source = tmp_path / "book.pdf"
        target = tmp_path / "chunk.pdf"

        writer = PdfWriter()
        for _ in range(20):
            writer.add_blank_page(width=100, height=100)

        # Embed a 1 MB orphan stream in the document catalog. PDFium
        # walks only references from imported pages so it will not copy
        # this; a clone-then-delete approach will keep it.
        orphan_payload = b"\x00" * (1024 * 1024)
        orphan_stream = DecodedStreamObject()
        orphan_stream.set_data(orphan_payload)
        orphan_ref = writer._add_object(orphan_stream)
        writer._root_object[NameObject("/MyOrphan")] = orphan_ref

        with source.open("wb") as fh:
            writer.write(fh)

        source_size = source.stat().st_size
        assert source_size > 1_000_000, (
            "fixture sanity: source must contain the orphan to be a "
            "meaningful regression target"
        )

        _extract_pdf_page_range(source, target, start_page=0, end_page=4)
        chunk_size = target.stat().st_size

        # 5 blank pages out of 20 should be a tiny fraction of the
        # source. Allow a generous ceiling (10% of source) so PDFium
        # version drift doesn't flake the test; the bug we are guarding
        # against produced chunks larger than the source.
        assert chunk_size < source_size * 0.10, (
            f"sub-PDF retained orphan resources from source: "
            f"src={source_size} bytes, chunk={chunk_size} bytes "
            f"({chunk_size / source_size:.0%}). Reverting "
            f"_extract_pdf_page_range to pypdf clone_from+del "
            f"would produce this regression."
        )

    def test_raises_when_start_page_past_eof(self, tmp_path):
        """A start_page past the source's last page is a caller bug.

        ``pypdfium2.import_pages`` treats an empty ``pages`` list as
        "import every page" — so without an explicit guard, a buggy
        range silently produces a full-document copy. Lock the guard
        in.
        """
        from revisica.ingestion.mineru_parser import _extract_pdf_page_range

        source = tmp_path / "book.pdf"
        target = tmp_path / "chunk.pdf"
        self._make_blank_pdf(source, num_pages=10)

        with pytest.raises(ValueError, match="past source EOF"):
            _extract_pdf_page_range(source, target, start_page=20, end_page=29)
        assert not target.exists()

    def test_raises_when_end_page_below_start_page(self, tmp_path):
        """Inverted range is a caller bug — must raise, not silently
        produce a full-document copy via pypdfium2's empty-list fallback."""
        from revisica.ingestion.mineru_parser import _extract_pdf_page_range

        source = tmp_path / "book.pdf"
        target = tmp_path / "chunk.pdf"
        self._make_blank_pdf(source, num_pages=10)

        with pytest.raises(ValueError, match="empty"):
            _extract_pdf_page_range(source, target, start_page=5, end_page=2)
        assert not target.exists()

    def test_raises_on_negative_start_page(self, tmp_path):
        from revisica.ingestion.mineru_parser import _extract_pdf_page_range

        source = tmp_path / "book.pdf"
        target = tmp_path / "chunk.pdf"
        self._make_blank_pdf(source, num_pages=10)

        with pytest.raises(ValueError, match=">= 0"):
            _extract_pdf_page_range(source, target, start_page=-1, end_page=4)


class TestMineruChunkRanges:
    def test_chunk_ranges_exact_division(self):
        from revisica.ingestion.mineru_parser import _chunk_ranges
        assert _chunk_ranges(60, 30) == [(0, 29), (30, 59)]

    def test_chunk_ranges_with_remainder(self):
        from revisica.ingestion.mineru_parser import _chunk_ranges
        assert _chunk_ranges(70, 30) == [(0, 29), (30, 59), (60, 69)]

    def test_chunk_ranges_smaller_than_chunk_size(self):
        from revisica.ingestion.mineru_parser import _chunk_ranges
        assert _chunk_ranges(10, 30) == [(0, 9)]

    def test_chunk_ranges_zero_pages(self):
        from revisica.ingestion.mineru_parser import _chunk_ranges
        assert _chunk_ranges(0, 30) == []


class TestMineruChunkingAndCache:
    """Auto-split + content-addressed resume for large PDFs."""

    def _patch_environment(self, monkeypatch, tmp_path, page_count):
        """Mock subprocess + page count + pypdf split + cache root."""
        from revisica.ingestion import mineru_parser as mp

        monkeypatch.setattr(mp.shutil, "which", lambda _name: "/usr/local/bin/mineru")
        monkeypatch.setattr(mp, "_count_pdf_pages", lambda _path: page_count)
        # Real ``_extract_pdf_page_range`` would call into PDFium, which
        # cannot parse the synthetic ``%PDF-1.4 fake`` byte strings used
        # throughout these tests; substitute a touch-a-file stub. The
        # production path is exercised by ``TestExtractPdfPageRange`` and
        # by ``revisica benchmark-ingestion`` on real PDFs.
        monkeypatch.setattr(
            mp, "_extract_pdf_page_range", _fake_extract_pdf_page_range
        )
        monkeypatch.setenv("REVISICA_MINERU_CHUNK_CACHE_DIR", str(tmp_path / "cache"))

    def test_small_pdf_is_not_chunked(self, monkeypatch, tmp_path):
        from revisica.ingestion import mineru_parser as mp

        self._patch_environment(monkeypatch, tmp_path, page_count=20)
        calls: list[dict[str, object]] = []
        monkeypatch.setattr(mp.subprocess, "run", _make_chunked_fake_mineru(calls))

        pdf = tmp_path / "paper.pdf"
        pdf.write_bytes(b"%PDF-1.4 fake")

        parser = mp.MineruParser(chunk_pages_threshold=50, chunk_pages_size=30)
        md = parser.parse(pdf)

        assert len(calls) == 1, "small PDF should be parsed in a single mineru call"
        assert calls[0]["start"] is None and calls[0]["end"] is None
        assert "chunk pages=None-None" in md

    def test_large_pdf_is_chunked_with_page_ranges(self, monkeypatch, tmp_path):
        from revisica.ingestion import mineru_parser as mp

        self._patch_environment(monkeypatch, tmp_path, page_count=70)
        calls: list[dict[str, object]] = []
        monkeypatch.setattr(mp.subprocess, "run", _make_chunked_fake_mineru(calls))

        pdf = tmp_path / "paper.pdf"
        pdf.write_bytes(b"%PDF-1.4 fake-large")

        parser = mp.MineruParser(chunk_pages_threshold=50, chunk_pages_size=30)
        md = parser.parse(pdf)

        assert [(c["start"], c["end"]) for c in calls] == [(0, 29), (30, 59), (60, 69)]
        assert "chunk pages=0-29" in md
        assert "chunk pages=30-59" in md
        assert "chunk pages=60-69" in md

    def test_resume_skips_cached_chunks(self, monkeypatch, tmp_path):
        """Second parse of the same PDF reads every chunk from cache."""
        from revisica.ingestion import mineru_parser as mp

        self._patch_environment(monkeypatch, tmp_path, page_count=70)
        calls: list[dict[str, object]] = []
        monkeypatch.setattr(mp.subprocess, "run", _make_chunked_fake_mineru(calls))

        pdf = tmp_path / "paper.pdf"
        pdf.write_bytes(b"%PDF-1.4 fake-resume")

        parser = mp.MineruParser(chunk_pages_threshold=50, chunk_pages_size=30)
        first = parser.parse(pdf)
        assert len(calls) == 3

        # Second pass: cache should win, no new subprocess calls.
        second = parser.parse(pdf)
        assert len(calls) == 3, "cache hits must not re-spawn mineru"
        assert first == second

    def test_partial_failure_resumes_from_next_chunk(self, monkeypatch, tmp_path):
        """If chunk 2 fails, a retry re-runs only chunk 2 + chunk 3."""
        from revisica.ingestion import mineru_parser as mp

        self._patch_environment(monkeypatch, tmp_path, page_count=70)

        attempts: list[dict[str, object]] = []
        good_runner = _make_chunked_fake_mineru(attempts)

        def flaky_runner(args, **kwargs):
            pdf_name = Path(args[args.index("-p") + 1]).name
            match = _CHUNK_PDF_NAME_RE.search(pdf_name)
            start = int(match.group(1)) if match else None
            # Fail on the second chunk during the *first* attempt only.
            if start == 30 and not flaky_runner.first_attempt_done:
                attempts.append({"start": 30, "end": 59, "failed": True})
                return subprocess.CompletedProcess(
                    args=args, returncode=1, stdout="", stderr="CUDA OOM"
                )
            return good_runner(args, **kwargs)

        flaky_runner.first_attempt_done = False  # type: ignore[attr-defined]
        monkeypatch.setattr(mp.subprocess, "run", flaky_runner)

        pdf = tmp_path / "paper.pdf"
        pdf.write_bytes(b"%PDF-1.4 fake-flaky")

        parser = mp.MineruParser(chunk_pages_threshold=50, chunk_pages_size=30)

        with pytest.raises(RuntimeError, match="CUDA OOM"):
            parser.parse(pdf)

        # First attempt: chunk 1 succeeded, chunk 2 failed before chunk 3 ran.
        successful_first_pass = [
            (a["start"], a["end"]) for a in attempts if not a.get("failed")
        ]
        assert successful_first_pass == [(0, 29)]

        # Allow chunk 2 to succeed on retry; clear the log to track attempt 2.
        flaky_runner.first_attempt_done = True  # type: ignore[attr-defined]
        attempts.clear()

        parser.parse(pdf)

        # Attempt 2 must skip chunk 1 (cached) and only run chunks 2 + 3.
        assert [(a["start"], a["end"]) for a in attempts] == [(30, 59), (60, 69)]

    def test_progress_callback_fires_for_each_chunk(self, monkeypatch, tmp_path):
        from revisica.ingestion import mineru_parser as mp

        self._patch_environment(monkeypatch, tmp_path, page_count=70)
        monkeypatch.setattr(mp.subprocess, "run", _make_chunked_fake_mineru([]))

        events: list[mp.MineruChunkProgress] = []
        parser = mp.MineruParser(
            chunk_pages_threshold=50,
            chunk_pages_size=30,
            progress_callback=events.append,
        )

        pdf = tmp_path / "paper.pdf"
        pdf.write_bytes(b"%PDF-1.4 fake-progress")
        parser.parse(pdf)

        # Each non-cached chunk fires running -> completed; with 3 chunks that is 6.
        assert len(events) == 6
        first = events[0]
        assert first.chunk_index == 1 and first.chunk_total == 3
        assert first.start_page == 0 and first.end_page == 29
        assert first.status == "running"
        assert events[1].status == "completed"

        # Re-parse: every chunk is cached, exactly one ``cached`` event each.
        events.clear()
        parser.parse(pdf)
        assert len(events) == 3
        assert all(e.status == "cached" for e in events)

    def test_clear_chunk_cache_removes_files(self, monkeypatch, tmp_path):
        from revisica.ingestion import mineru_parser as mp

        self._patch_environment(monkeypatch, tmp_path, page_count=70)
        monkeypatch.setattr(mp.subprocess, "run", _make_chunked_fake_mineru([]))

        pdf = tmp_path / "paper.pdf"
        pdf.write_bytes(b"%PDF-1.4 fake-clear")

        parser = mp.MineruParser(chunk_pages_threshold=50, chunk_pages_size=30)
        parser.parse(pdf)
        assert mp.chunk_cache_root().exists()

        removed = mp.clear_chunk_cache()
        assert removed == 3
        assert not mp.chunk_cache_root().exists()

    def test_progress_callback_reports_failed_chunk(self, monkeypatch, tmp_path):
        """When MinerU raises mid-parse, the failing chunk emits a 'failed'
        event so the UI can flip its row off ``running`` instead of leaving
        it stuck."""
        from revisica.ingestion import mineru_parser as mp

        self._patch_environment(monkeypatch, tmp_path, page_count=70)

        def runner(args, **kwargs):
            pdf_path = Path(args[args.index("-p") + 1])
            match = _CHUNK_PDF_NAME_RE.search(pdf_path.name)
            start = int(match.group(1)) if match else None
            if start == 30:
                return subprocess.CompletedProcess(
                    args=args, returncode=1, stdout="", stderr="CUDA OOM"
                )
            out_dir = Path(args[args.index("-o") + 1])
            target_dir = out_dir / pdf_path.stem
            target_dir.mkdir(parents=True, exist_ok=True)
            (target_dir / f"{pdf_path.stem}.md").write_text(
                "# chunk ok\n", encoding="utf-8"
            )
            return subprocess.CompletedProcess(args=args, returncode=0, stdout="", stderr="")

        monkeypatch.setattr(mp.subprocess, "run", runner)

        events: list[mp.MineruChunkProgress] = []
        parser = mp.MineruParser(
            chunk_pages_threshold=50,
            chunk_pages_size=30,
            progress_callback=events.append,
        )
        pdf = tmp_path / "paper.pdf"
        pdf.write_bytes(b"%PDF-1.4 fake-failed")

        with pytest.raises(RuntimeError, match="CUDA OOM"):
            parser.parse(pdf)

        # Chunk 1 ran to completion (running, completed); chunk 2 ran then
        # raised (running, failed). Chunk 3 is never reached.
        statuses = [(e.start_page, e.status) for e in events]
        assert statuses == [
            (0, "running"), (0, "completed"),
            (30, "running"), (30, "failed"),
        ]

    def test_atomic_write_does_not_leave_tmp_files(self, monkeypatch, tmp_path):
        """A fresh cache directory only contains finalized ``*.md`` files."""
        from revisica.ingestion import mineru_parser as mp

        self._patch_environment(monkeypatch, tmp_path, page_count=70)
        monkeypatch.setattr(mp.subprocess, "run", _make_chunked_fake_mineru([]))

        pdf = tmp_path / "paper.pdf"
        pdf.write_bytes(b"%PDF-1.4 fake-atomic")

        mp.MineruParser(chunk_pages_threshold=50, chunk_pages_size=30).parse(pdf)
        leftovers = list(mp.chunk_cache_root().rglob("*.tmp"))
        assert leftovers == []
