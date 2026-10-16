"""Unified review graph: routing, lane concurrency, and option plumbing.

Regression coverage for three gaps: the writing and math lanes ran one
after the other despite being documented as concurrent; polish mode
skipped ingestion and handed raw PDF bytes to the polish graph; and
``--codex-reasoning`` was dropped before reaching either review lane.
"""

from __future__ import annotations

import threading
from pathlib import Path

import pytest

import revisica.graphs.polish as polish_graph_module
import revisica.graphs.unified as unified
import revisica.graphs.writing as writing_graph_module
from revisica.ingestion.types import RevisicaDocument
from revisica.profiles.config import ReviewConfig, ReviewMode

_PDF_BYTES = b"%PDF-1.7\n%\xa1\xb3\xc5\xd7\n1 0 obj\n<<>>\nendobj\n"
_NORMALIZED_MARKDOWN = "# Introduction\n\nWe study optimal partitions.\n"
_LANE_OVERLAP_TIMEOUT_SECONDS = 5


def _write_pdf(directory: Path) -> Path:
    pdf_path = directory / "paper.pdf"
    pdf_path.write_bytes(_PDF_BYTES)
    return pdf_path


def _fake_ingest(state: dict) -> dict:
    return {
        "document": RevisicaDocument(
            source_path=state["source_path"],
            parser_used="mineru",
            markdown=_NORMALIZED_MARKDOWN,
        )
    }


class _RecordingGraph:
    def __init__(self, final_state: dict) -> None:
        self.invoked_states: list[dict] = []
        self._final_state = final_state

    def invoke(self, state: dict) -> dict:
        self.invoked_states.append(state)
        return self._final_state


def test_review_lanes_run_concurrently(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # Each fake lane blocks until the other lane is running too, so a
    # sequential graph breaks the barrier instead of passing.
    both_lanes_running = threading.Barrier(2, timeout=_LANE_OVERLAP_TIMEOUT_SECONDS)

    def fake_writing_lane(state: dict) -> dict:
        both_lanes_running.wait()
        return {"writing_result": None, "warnings": ["writing lane ran"]}

    def fake_math_lane(state: dict) -> dict:
        both_lanes_running.wait()
        return {"math_result": None, "warnings": ["math lane ran"]}

    monkeypatch.setattr(unified, "ingest_document", _fake_ingest)
    monkeypatch.setattr(unified, "run_writing_lane", fake_writing_lane)
    monkeypatch.setattr(unified, "run_math_lane", fake_math_lane)

    pdf_path = _write_pdf(tmp_path)
    run_dir = tmp_path / "run"
    final_state = unified.build_unified_graph().compile().invoke({
        "source_path": str(pdf_path),
        "run_dir": str(run_dir),
        "config": ReviewConfig(),
        "warnings": [],
    })

    assert sorted(final_state["warnings"]) == ["math lane ran", "writing lane ran"]
    assert final_state["unified_review_run"].run_dir == run_dir
    assert (run_dir / "summary.md").is_file()


def test_polish_mode_reviews_ingested_markdown(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    recording_polish_graph = _RecordingGraph({"warnings": []})
    monkeypatch.setattr(unified, "ingest_document", _fake_ingest)
    monkeypatch.setattr(polish_graph_module, "compile_polish_graph", lambda: recording_polish_graph)

    pdf_path = _write_pdf(tmp_path)
    run_dir = tmp_path / "run"
    final_state = unified.build_unified_graph().compile().invoke({
        "source_path": str(pdf_path),
        "run_dir": str(run_dir),
        "config": ReviewConfig(mode=ReviewMode.POLISH),
        "warnings": [],
    })

    assert final_state["warnings"] == []
    polished_path = Path(recording_polish_graph.invoked_states[0]["source_path"])
    assert polished_path == run_dir / "paper.normalized.md"
    assert polished_path.read_text(encoding="utf-8") == _NORMALIZED_MARKDOWN


def test_codex_reasoning_effort_reaches_writing_lane(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    recording_writing_graph = _RecordingGraph({"writing_review_run": None})
    monkeypatch.setattr(writing_graph_module, "compile_writing_graph", lambda: recording_writing_graph)

    tex_path = tmp_path / "paper.tex"
    tex_path.write_text("\\section{Intro}\n", encoding="utf-8")
    unified.run_writing_lane({
        "source_path": str(tex_path),
        "run_dir": str(tmp_path / "run"),
        "config": ReviewConfig(codex_reasoning_effort="high"),
    })

    writing_config = recording_writing_graph.invoked_states[0]["config"]
    assert writing_config.codex_reasoning_effort == "high"


def test_codex_reasoning_effort_reaches_math_lane(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    math_review_calls: list[dict] = []

    def record_review_math_file(**kwargs):
        math_review_calls.append(kwargs)

    monkeypatch.setattr(unified, "review_math_file", record_review_math_file)

    tex_path = tmp_path / "paper.tex"
    tex_path.write_text("\\section{Intro}\n", encoding="utf-8")
    unified.run_math_lane({
        "source_path": str(tex_path),
        "run_dir": str(tmp_path / "run"),
        "config": ReviewConfig(codex_reasoning_effort="high"),
    })

    assert math_review_calls[0]["codex_reasoning_effort"] == "high"
