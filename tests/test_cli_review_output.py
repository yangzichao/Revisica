"""`revisica review` must describe what the chosen mode actually ran.

Polish mode runs neither the writing nor the math lane, so both are always
``None`` on the result. The CLI used to report that as two failed lanes.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

import revisica.cli as cli
from revisica.unified_review import UnifiedReviewRun


def _run_review_cli(
    monkeypatch: pytest.MonkeyPatch,
    paper_path: Path,
    mode: str,
    warnings: list[str],
) -> None:
    def fake_review_unified(**kwargs) -> UnifiedReviewRun:
        assert kwargs["mode"] == mode
        return UnifiedReviewRun(
            source=paper_path,
            run_dir=paper_path.parent / "run",
            writing=None,
            math=None,
            warnings=warnings,
        )

    monkeypatch.setattr(cli, "review_unified", fake_review_unified)
    monkeypatch.setattr(sys, "argv", ["revisica", "review", str(paper_path), "--mode", mode])
    cli.main()


def test_polish_mode_reports_polish_report_not_failed_lanes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    paper_path = tmp_path / "paper.pdf"
    paper_path.write_bytes(b"%PDF-1.4")

    _run_review_cli(monkeypatch, paper_path, "polish", warnings=[])

    output = capsys.readouterr().out
    assert "lane: failed" not in output
    assert f"polish report: {tmp_path / 'run' / 'polish_report.md'}" in output


def test_polish_mode_surfaces_agent_failure_as_warning(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    paper_path = tmp_path / "paper.tex"
    paper_path.write_text("text", encoding="utf-8")

    _run_review_cli(monkeypatch, paper_path, "polish", warnings=["Polish agent failed: timeout"])

    assert "warning: Polish agent failed: timeout" in capsys.readouterr().out


def test_review_mode_still_reports_missing_lanes_as_failed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    paper_path = tmp_path / "paper.tex"
    paper_path.write_text("text", encoding="utf-8")

    _run_review_cli(monkeypatch, paper_path, "review", warnings=[])

    output = capsys.readouterr().out
    assert "writing lane: failed" in output
    assert "math lane: failed" in output
