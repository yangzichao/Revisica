"""The deterministic math-cases suite must stay fully passing.

This is the "quickest sanity check" from CLAUDE.md
(``revisica benchmark-run --suite math-cases --mode deterministic-only``)
as a test. The CLI exits 0 even when cases fail, so without this a CI
run would not notice a regression in the deterministic math engine.
"""

from __future__ import annotations

from pathlib import Path

from revisica.eval.framework import run_benchmark

_MATH_CASES_MANIFEST = Path(__file__).resolve().parents[1] / "benchmarks" / "math" / "manifest.json"


def test_every_math_case_passes_deterministically(tmp_path: Path) -> None:
    benchmark = run_benchmark(
        suite="math-cases",
        mode="deterministic-only",
        output_dir=str(tmp_path / "math-cases"),
        manifest=str(_MATH_CASES_MANIFEST),
    )

    failing_cases = {
        case_run.case_id: case_run.pass_message
        for case_run in benchmark.cases
        if case_run.passed is not True
    }
    assert benchmark.cases
    assert failing_cases == {}
