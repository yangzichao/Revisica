from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import json
from pathlib import Path

from .provenance import (
    RegistryEntry,
    append_to_registry,
    build_provenance,
)
from ..writing_review import WritingReviewRun, review_writing_file


@dataclass
class WritingBenchmarkCaseResult:
    case_id: str
    passed: bool
    message: str
    run_dir: Path


def run_writing_benchmark(
    manifest_path: str,
    venue_profile: str | None = None,
    force_bootstrap: bool = False,
    timeout_seconds: int = 120,
) -> tuple[list[WritingBenchmarkCaseResult], Path]:
    manifest_file = Path(manifest_path).expanduser().resolve()
    base_dir = manifest_file.parent
    payload = json.loads(manifest_file.read_text(encoding="utf-8"))
    results: list[WritingBenchmarkCaseResult] = []
    report_dir = _make_report_dir(base_dir)

    for case in payload["cases"]:
        source = base_dir / case["file"]
        profile = venue_profile or case.get("expected", {}).get("venue_profile", "general-academic")
        run = review_writing_file(
            str(source),
            output_dir=str(report_dir / case["id"]),
            venue_profile=profile,
            force_bootstrap=force_bootstrap,
            timeout_seconds=timeout_seconds,
        )
        passed, message = _evaluate_case(run, case.get("expected", {}))
        results.append(
            WritingBenchmarkCaseResult(
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

    provenance = build_provenance(
        suite="writing",
        extra={"venue_profile": venue_profile},
    )
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
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    report_dir = base_dir / "runs" / stamp
    report_dir.mkdir(parents=True, exist_ok=True)
    return report_dir


def _evaluate_case(
    run: WritingReviewRun,
    expected: dict[str, object],
) -> tuple[bool, str]:
    basic_findings = _count_findings_by_role(run, "basic")
    structure_findings = _count_findings_by_role(run, "structure")
    venue_findings = _count_findings_by_role(run, "venue")
    all_findings = _collect_all_findings(run)
    critical_count = sum(1 for f in all_findings if f.get("severity") == "critical")
    major_count = sum(1 for f in all_findings if f.get("severity") == "major")

    failures: list[str] = []

    minimum_basic = int(expected.get("minimum_basic_findings", 0) or 0)
    if basic_findings < minimum_basic:
        failures.append(f"basic findings {basic_findings} < expected minimum {minimum_basic}")

    minimum_structure = int(expected.get("minimum_structure_findings", 0) or 0)
    if structure_findings < minimum_structure:
        failures.append(f"structure findings {structure_findings} < expected minimum {minimum_structure}")

    minimum_venue = int(expected.get("minimum_venue_findings", 0) or 0)
    if venue_findings < minimum_venue:
        failures.append(f"venue findings {venue_findings} < expected minimum {minimum_venue}")

    max_critical = expected.get("maximum_critical_findings")
    if max_critical is not None and critical_count > int(max_critical):
        failures.append(f"critical findings {critical_count} > expected maximum {max_critical}")

    max_major = expected.get("maximum_major_findings")
    if max_major is not None and major_count > int(max_major):
        failures.append(f"major findings {major_count} > expected maximum {max_major}")

    expected_cats = expected.get("expected_categories")
    if expected_cats:
        found_cats = {f.get("category") for f in all_findings if f.get("category")}
        missing_cats = [cat for cat in expected_cats if cat not in found_cats]
        if missing_cats:
            failures.append(f"missing expected categories: {', '.join(missing_cats)}")

    if failures:
        return False, "; ".join(failures)
    return True, f"ok (basic={basic_findings}, structure={structure_findings}, venue={venue_findings})"


def _count_findings_by_role(run: WritingReviewRun, role: str) -> int:
    total = 0
    for artifact in run.artifacts:
        if artifact.role == role and artifact.findings is not None:
            total += len(artifact.findings)
    return total


def _collect_all_findings(run: WritingReviewRun) -> list[dict[str, object]]:
    findings: list[dict[str, object]] = []
    for artifact in run.artifacts:
        if artifact.findings is not None:
            findings.extend(artifact.findings)
    return findings


def _render_summary(summary: dict[str, object]) -> str:
    lines = [
        "# Revisica Writing Benchmark",
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
