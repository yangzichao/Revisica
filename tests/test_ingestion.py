"""Tests for the ingestion layer: parsers, normalize, and registry."""

from __future__ import annotations

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


def _make_chunked_fake_mineru(call_log: list[dict[str, object]]):
    """Build a ``subprocess.run`` fake that records the chunk slice and
    writes a deterministic chunk-marker markdown file into the output dir."""

    def runner(args, *, capture_output, text, check, timeout):
        out_dir = Path(args[args.index("-o") + 1])
        start = int(args[args.index("-s") + 1]) if "-s" in args else None
        end = int(args[args.index("-e") + 1]) if "-e" in args else None
        call_log.append({"start": start, "end": end})

        target_dir = out_dir / "paper"
        target_dir.mkdir(parents=True, exist_ok=True)
        marker = f"# chunk pages={start}-{end}\n\nbody for {start}-{end}\n"
        (target_dir / "paper.md").write_text(marker, encoding="utf-8")

        return subprocess.CompletedProcess(args=args, returncode=0, stdout="", stderr="")

    return runner


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
        """Mock subprocess + page count + redirect cache root into ``tmp_path``."""
        from revisica.ingestion import mineru_parser as mp

        monkeypatch.setattr(mp.shutil, "which", lambda _name: "/usr/local/bin/mineru")
        monkeypatch.setattr(mp, "_count_pdf_pages", lambda _path: page_count)
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
            start = int(args[args.index("-s") + 1])
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
            start = int(args[args.index("-s") + 1])
            if start == 30:
                return subprocess.CompletedProcess(
                    args=args, returncode=1, stdout="", stderr="CUDA OOM"
                )
            out_dir = Path(args[args.index("-o") + 1])
            target_dir = out_dir / "paper"
            target_dir.mkdir(parents=True, exist_ok=True)
            (target_dir / "paper.md").write_text("# chunk ok\n", encoding="utf-8")
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
