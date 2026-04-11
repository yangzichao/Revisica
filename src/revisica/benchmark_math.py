from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path

from .benchmark_provenance import (
    RegistryEntry,
    append_to_registry,
    build_provenance,
)
from .math_review import MathReviewRun, review_math_file


@dataclass
class BenchmarkCaseResult:
    case_id: str
    passed: bool
    message: str
    run_dir: Path


def run_math_benchmark(manifest_path: str) -> tuple[list[BenchmarkCaseResult], Path]:
    manifest_file = Path(manifest_path).expanduser().resolve()
    base_dir = manifest_file.parent
    payload = json.loads(manifest_file.read_text(encoding="utf-8"))
    results: list[BenchmarkCaseResult] = []
    report_dir = _make_report_dir(base_dir)

    for case in payload["cases"]:
        source = base_dir / case["file"]
        run = review_math_file(str(source), output_dir=str(report_dir / case["id"]))
        passed, message = _evaluate_case(run, case["expected"])
        results.append(
            BenchmarkCaseResult(
                case_id=case["id"],
                passed=passed,
                message=message,
                run_dir=run.run_dir,
            )
        )

    summary = {
        "manifest": str(manifest_file),
        "passed": sum(1 for item in results if item.passed),
        "total": len(results),
        "results": [
            {
                "case_id": item.case_id,
                "passed": item.passed,
                "message": item.message,
                "run_dir": str(item.run_dir),
            }
            for item in results
        ],
    }
    (report_dir / "benchmark_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )
    (report_dir / "benchmark_summary.md").write_text(
        _render_summary(summary),
        encoding="utf-8",
    )

    provenance = build_provenance(suite="math")
    entry = RegistryEntry(
        provenance=provenance,
        passed=summary["passed"],
        total=summary["total"],
        case_results=summary["results"],
        report_dir=str(report_dir),
    )
    append_to_registry(entry)

    return results, report_dir


def _make_report_dir(base_dir: Path) -> Path:
    report_dir = base_dir / "runs"
    report_dir.mkdir(parents=True, exist_ok=True)
    return report_dir


def _evaluate_case(run: MathReviewRun, expected: dict[str, object]) -> tuple[bool, str]:
    refuted_titles = {item.title for item in run.issues if item.status == "machine-refuted"}
    verified_titles = {item.title for item in run.issues if item.status == "machine-verified"}
    needs_human_check = sum(1 for item in run.issues if item.status == "needs-human-check")

    missing_refuted = [
        title for title in expected.get("machine_refuted_titles", []) if title not in refuted_titles
    ]
    missing_verified = [
        title for title in expected.get("machine_verified_titles", []) if title not in verified_titles
    ]
    minimum_needs_human_check = int(expected.get("minimum_needs_human_check", 0) or 0)
    minimum_blueprints = int(expected.get("minimum_blueprints", 0) or 0)

    failures: list[str] = []
    if missing_refuted:
        failures.append(f"missing machine-refuted titles: {', '.join(missing_refuted)}")
    if missing_verified:
        failures.append(f"missing machine-verified titles: {', '.join(missing_verified)}")
    if needs_human_check < minimum_needs_human_check:
        failures.append(
            f"needs-human-check count {needs_human_check} < expected minimum {minimum_needs_human_check}"
        )
    if len(run.blueprints) < minimum_blueprints:
        failures.append(f"blueprints {len(run.blueprints)} < expected minimum {minimum_blueprints}")

    if failures:
        return False, "; ".join(failures)
    return True, "ok"


def _render_summary(summary: dict[str, object]) -> str:
    lines = [
        "# Revisica Math Benchmark",
        "",
        f"- Manifest: `{summary['manifest']}`",
        f"- Passed: `{summary['passed']}` / `{summary['total']}`",
        "",
        "## Cases",
        "",
    ]
    for result in summary["results"]:
        status = "PASS" if result["passed"] else "FAIL"
        lines.append(
            f"- `{result['case_id']}`: {status} — {result['message']} (`{result['run_dir']}`)"
        )
    return "\n".join(lines) + "\n"
