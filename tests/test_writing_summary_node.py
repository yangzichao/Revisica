"""The writing graph's final node must write summary.md, not call itself."""

from __future__ import annotations

from pathlib import Path

from revisica.graphs.nodes.writing import write_summary


def test_write_summary_node_writes_summary_file(tmp_path: Path):
    source_path = tmp_path / "paper.tex"
    source_path.write_text("\\section{Intro}\nText.\n", encoding="utf-8")
    run_dir = tmp_path / "writing"
    run_dir.mkdir()

    node_output = write_summary({
        "source_path": str(source_path),
        "run_dir": str(run_dir),
        "venue_profile": "general-academic",
    })

    assert node_output["writing_review_run"].run_dir == run_dir
    assert (run_dir / "summary.md").exists()
