"""Tests for the ingestion layer: parsers, normalize, and registry."""

from __future__ import annotations

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


# ── MinerU parser (import + availability only) ────────────────────────


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
