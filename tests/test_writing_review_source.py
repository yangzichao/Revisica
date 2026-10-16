"""The writing lane must review text, never raw PDF bytes.

Regression coverage for ``revisica review paper.pdf``, where the writing
lane ignored the ingested document and crashed with ``UnicodeDecodeError``
on the PDF.
"""

from __future__ import annotations

from pathlib import Path

import pytest

import revisica.graphs.writing as writing_graph_module
from revisica.graphs.nodes.writing import bootstrap_and_extract
from revisica.graphs.unified import run_writing_lane
from revisica.ingestion.types import RevisicaDocument
from revisica.profiles.config import ReviewConfig
from revisica.writing.review_source import prepare_writing_source

_PDF_BYTES = b"%PDF-1.7\n%\xa1\xb3\xc5\xd7\n1 0 obj\n<<>>\nendobj\n"
_NORMALIZED_MARKDOWN = "# Introduction\n\nWe study optimal partitions.\n"


def _write_pdf(directory: Path) -> Path:
    pdf_path = directory / "paper.pdf"
    pdf_path.write_bytes(_PDF_BYTES)
    return pdf_path


def _ingested_document(pdf_path: Path) -> RevisicaDocument:
    return RevisicaDocument(
        source_path=str(pdf_path),
        parser_used="mineru",
        markdown=_NORMALIZED_MARKDOWN,
    )


def test_text_sources_are_reviewed_as_is(tmp_path: Path) -> None:
    tex_path = tmp_path / "paper.tex"
    tex_path.write_text("\\section{Intro}\n", encoding="utf-8")

    assert prepare_writing_source(str(tex_path), None, tmp_path / "writing") == str(tex_path)


def test_pdf_source_uses_ingested_markdown(tmp_path: Path) -> None:
    pdf_path = _write_pdf(tmp_path)
    writing_dir = tmp_path / "run" / "writing"

    review_path = Path(
        prepare_writing_source(str(pdf_path), _ingested_document(pdf_path), writing_dir)
    )

    assert review_path == writing_dir / "paper.normalized.md"
    assert review_path.read_text(encoding="utf-8") == _NORMALIZED_MARKDOWN


def test_pdf_source_without_ingestion_fails_clearly(tmp_path: Path) -> None:
    pdf_path = _write_pdf(tmp_path)

    with pytest.raises(ValueError, match="not a plain-text source"):
        prepare_writing_source(str(pdf_path), None, tmp_path / "writing")


def test_standalone_writing_graph_rejects_binary_source(tmp_path: Path) -> None:
    pdf_path = _write_pdf(tmp_path)

    with pytest.raises(ValueError, match="plain-text source"):
        bootstrap_and_extract({
            "source_path": str(pdf_path),
            "run_dir": str(tmp_path / "run"),
            "config": ReviewConfig(),
        })


def test_unified_writing_lane_reviews_normalized_markdown(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pdf_path = _write_pdf(tmp_path)
    run_dir = tmp_path / "run"
    invoked_states: list[dict] = []

    class RecordingGraph:
        def invoke(self, state: dict) -> dict:
            invoked_states.append(state)
            return {"writing_review_run": None}

    monkeypatch.setattr(writing_graph_module, "compile_writing_graph", lambda: RecordingGraph())

    lane_update = run_writing_lane({
        "source_path": str(pdf_path),
        "run_dir": str(run_dir),
        "config": ReviewConfig(),
        "document": _ingested_document(pdf_path),
        "warnings": [],
    })

    assert lane_update["warnings"] == []
    reviewed_path = Path(invoked_states[0]["source_path"])
    assert reviewed_path == run_dir / "writing" / "paper.normalized.md"
    assert reviewed_path.read_text(encoding="utf-8") == _NORMALIZED_MARKDOWN
