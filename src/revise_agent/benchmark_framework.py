from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import json
from pathlib import Path
import re

from .math_review import MathReviewRun, review_math_file
from .processbench_adapter import import_processbench_cases
from .proofbench_adapter import import_proofbench_cases
from .proofnet_adapter import import_proofnet_cases
from .core_types import ProviderModelSpec


BENCHMARK_MODES = {
    "deterministic-only",
    "single-agent",
    "single-agent-self-check",
    "multi-agent-cross-check",
    "hybrid-single",
    "hybrid-cross",
}

BENCHMARK_SUITES = {
    "math-cases",
    "proofnet",
    "proofbench",
    "processbench",
    "all",
}


@dataclass
class BenchmarkRoles:
    reviewer: ProviderModelSpec | None
    reviewer_a: ProviderModelSpec | None
    reviewer_b: ProviderModelSpec | None
    self_checker: ProviderModelSpec | None
    adjudicator: ProviderModelSpec | None


@dataclass
class BenchmarkCaseRun:
    case_id: str
    source: Path
    run_dir: Path
    machine_refuted: int
    machine_verified: int
    llm_suspected: int
    needs_human_check: int
    blueprints: int
    llm_provider_reviews: int
    llm_self_checks: int
    llm_adjudications: int
    warnings: list[str]
    passed: bool | None
    pass_message: str | None
    metadata: dict[str, object]


@dataclass
class BenchmarkRun:
    suite: str
    mode: str
    report_dir: Path
    roles: BenchmarkRoles
    cases: list[BenchmarkCaseRun]


BenchmarkCase = dict[str, object]


def parse_provider_model_spec(text: str | None) -> ProviderModelSpec | None:
    if text is None:
        return None
    raw = text.strip()
    if not raw:
        return None
    if ":" in raw:
        provider, model = raw.split(":", 1)
        return ProviderModelSpec(provider=provider.strip(), model=model.strip() or None)
    return ProviderModelSpec(provider=raw, model=None)


def run_benchmark(
    suite: str,
    mode: str,
    output_dir: str | None = None,
    manifest: str | None = None,
    split: str = "test",
    limit: int = 10,
    reviewer: ProviderModelSpec | None = None,
    reviewer_a: ProviderModelSpec | None = None,
    reviewer_b: ProviderModelSpec | None = None,
    self_checker: ProviderModelSpec | None = None,
    adjudicator: ProviderModelSpec | None = None,
    force_bootstrap: bool = False,
    timeout_seconds: int = 120,
) -> BenchmarkRun:
    normalized_suite = _normalize_suite(suite)
    normalized_mode = _normalize_mode(mode)
    roles = _resolve_roles(
        mode=normalized_mode,
        reviewer=reviewer,
        reviewer_a=reviewer_a,
        reviewer_b=reviewer_b,
        self_checker=self_checker,
        adjudicator=adjudicator,
    )
    report_dir = _make_benchmark_dir(normalized_suite, normalized_mode, output_dir)
    cases = _SUITE_LOADERS[normalized_suite](manifest=manifest, split=split, limit=limit)

    case_runs: list[BenchmarkCaseRun] = []
    for case in cases:
        case_dir = report_dir / _slugify_case_id(case["id"])
        run = _run_case(
            source=case["source"],
            output_dir=str(case_dir),
            mode=normalized_mode,
            roles=roles,
            force_bootstrap=force_bootstrap,
            timeout_seconds=timeout_seconds,
        )
        passed, pass_message = _evaluate_expected(run, case.get("expected"))
        case_runs.append(
            BenchmarkCaseRun(
                case_id=case["id"],
                source=case["source"],
                run_dir=run.run_dir,
                machine_refuted=sum(1 for item in run.issues if item.status == "machine-refuted"),
                machine_verified=sum(1 for item in run.issues if item.status == "machine-verified"),
                llm_suspected=sum(1 for item in run.issues if item.status == "llm-suspected"),
                needs_human_check=sum(1 for item in run.issues if item.status == "needs-human-check"),
                blueprints=len(run.blueprints),
                llm_provider_reviews=len(run.llm_provider_results),
                llm_self_checks=len(run.llm_self_check_results),
                llm_adjudications=len(run.llm_adjudication_results),
                warnings=run.warnings,
                passed=passed,
                pass_message=pass_message,
                metadata=dict(case.get("metadata", {})),
            )
        )

    benchmark = BenchmarkRun(
        suite=normalized_suite,
        mode=normalized_mode,
        report_dir=report_dir,
        roles=roles,
        cases=case_runs,
    )
    _write_benchmark_summary(benchmark)
    return benchmark


def _normalize_suite(suite: str) -> str:
    normalized = suite.lower()
    if normalized not in BENCHMARK_SUITES:
        raise ValueError(
            "suite must be one of `math-cases`, `proofnet`, `proofbench`, `processbench`, or `all`."
        )
    return normalized


def _normalize_proofnet_split(split: str) -> str:
    return split if split in {"test", "valid"} else "test"


def _normalize_processbench_split(split: str) -> str:
    return split if split in {"gsm8k", "math", "olympiadbench", "omnimath"} else "math"


def _normalize_mode(mode: str) -> str:
    normalized = mode.lower()
    if normalized not in BENCHMARK_MODES:
        raise ValueError(
            "mode must be one of deterministic-only, single-agent, "
            "single-agent-self-check, multi-agent-cross-check, hybrid-single, hybrid-cross."
        )
    return normalized


def _make_benchmark_dir(suite: str, mode: str, output_dir: str | None) -> Path:
    if output_dir:
        target = Path(output_dir).expanduser().resolve()
    else:
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        target = Path.cwd() / "benchmarks" / "runs" / f"{suite}-{mode}-{stamp}"
    target.mkdir(parents=True, exist_ok=True)
    return target


def _load_local_math_cases(manifest: str | None) -> list[dict[str, object]]:
    manifest_path = (
        Path(manifest).expanduser().resolve()
        if manifest
        else Path.cwd() / "benchmarks" / "math" / "manifest.json"
    )
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    base_dir = manifest_path.parent
    return [
        {
            "id": case["id"],
            "source": base_dir / case["file"],
            "expected": case.get("expected"),
            "metadata": {
                "source_suite": "math-cases",
            },
        }
        for case in payload["cases"]
    ]


def _load_math_suite_cases(
    manifest: str | None,
    split: str,
    limit: int,
) -> list[BenchmarkCase]:
    del split, limit
    return _load_local_math_cases(manifest)


def _load_proofnet_suite_cases(
    manifest: str | None,
    split: str,
    limit: int,
) -> list[BenchmarkCase]:
    del manifest
    imported = import_proofnet_cases(split=_normalize_proofnet_split(split), limit=limit)
    payload = json.loads(imported.manifest_path.read_text(encoding="utf-8"))
    return [
        {
            "id": case["id"],
            "source": imported.output_dir / case["file"],
            "expected": None,
            "metadata": {
                "source_suite": "proofnet",
            },
        }
        for case in payload["cases"]
    ]


def _load_proofbench_suite_cases(
    manifest: str | None,
    split: str,
    limit: int,
) -> list[BenchmarkCase]:
    del manifest, split
    imported = import_proofbench_cases(split="train", limit=limit)
    payload = json.loads(imported.manifest_path.read_text(encoding="utf-8"))
    return [
        {
            "id": case["id"],
            "source": imported.output_dir / case["file"],
            "expected": None,
            "metadata": {
                "source_suite": "proofbench",
                "expert_rating": case["expert_rating"],
                "generator": case["generator"],
                "problem_id": case["problem_id"],
                "contest": case["contest"],
                "contest_year": case["contest_year"],
            },
        }
        for case in payload["cases"]
    ]


def _load_processbench_suite_cases(
    manifest: str | None,
    split: str,
    limit: int,
) -> list[BenchmarkCase]:
    del manifest
    imported = import_processbench_cases(split=_normalize_processbench_split(split), limit=limit)
    payload = json.loads(imported.manifest_path.read_text(encoding="utf-8"))
    return [
        {
            "id": case["id"],
            "source": imported.output_dir / case["file"],
            "expected": case.get("expected"),
            "metadata": {
                "source_suite": "processbench",
                "generator": case["generator"],
                "label": case["label"],
                "final_answer_correct": case["final_answer_correct"],
                "steps": case["steps"],
            },
        }
        for case in payload["cases"]
    ]


def _load_all_suite_cases(
    manifest: str | None,
    split: str,
    limit: int,
) -> list[BenchmarkCase]:
    cases: list[BenchmarkCase] = []
    cases.extend(_load_math_suite_cases(manifest, split, limit))
    cases.extend(_prefix_case_ids(_load_proofnet_suite_cases(None, split, limit), "proofnet"))
    cases.extend(_prefix_case_ids(_load_proofbench_suite_cases(None, split, limit), "proofbench"))
    cases.extend(_prefix_case_ids(_load_processbench_suite_cases(None, split, limit), "processbench"))
    return cases


def _prefix_case_ids(cases: list[BenchmarkCase], prefix: str) -> list[BenchmarkCase]:
    return [
        {
            **case,
            "id": f"{prefix}::{case['id']}",
        }
        for case in cases
    ]


def _resolve_roles(
    mode: str,
    reviewer: ProviderModelSpec | None,
    reviewer_a: ProviderModelSpec | None,
    reviewer_b: ProviderModelSpec | None,
    self_checker: ProviderModelSpec | None,
    adjudicator: ProviderModelSpec | None,
) -> BenchmarkRoles:
    if mode == "deterministic-only":
        return BenchmarkRoles(None, None, None, None, None)
    if mode in {"single-agent", "single-agent-self-check", "hybrid-single"}:
        primary = reviewer or reviewer_a or ProviderModelSpec(provider="codex")
        checker = self_checker if mode == "single-agent-self-check" else None
        return BenchmarkRoles(primary, None, None, checker, adjudicator)

    first = reviewer_a or reviewer or ProviderModelSpec(provider="codex")
    second = reviewer_b or ProviderModelSpec(provider="claude")
    return BenchmarkRoles(None, first, second, self_checker, adjudicator)


def _run_case(
    source: Path,
    output_dir: str,
    mode: str,
    roles: BenchmarkRoles,
    force_bootstrap: bool,
    timeout_seconds: int,
) -> MathReviewRun:
    runner = _MODE_RUNNERS[mode]
    kwargs = runner(roles)
    return review_math_file(
        file_path=str(source),
        output_dir=output_dir,
        **kwargs,
        force_bootstrap=force_bootstrap,
        timeout_seconds=timeout_seconds,
    )


def _evaluate_expected(run: MathReviewRun, expected: dict[str, object] | None) -> tuple[bool | None, str | None]:
    if expected is None:
        return None, None
    if "expected_first_issue_step_zero_based" in expected:
        expected_step = int(expected["expected_first_issue_step_zero_based"])
        predicted_step = _extract_earliest_issue_step(run)
        if expected_step == -1 and predicted_step is None:
            return True, "ok"
        if expected_step == predicted_step:
            return True, "ok"
        return False, f"predicted first issue step {predicted_step} != expected {expected_step}"
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


def _extract_earliest_issue_step(run: MathReviewRun) -> int | None:
    steps: list[int] = []
    for issue in run.issues:
        match = re.search(r"Step (\d+):", issue.snippet)
        if match:
            steps.append(int(match.group(1)))
    if not steps:
        return None
    return min(steps)


def _write_benchmark_summary(benchmark: BenchmarkRun) -> None:
    suite_metrics = _compute_suite_metrics(benchmark)
    payload = {
        "suite": benchmark.suite,
        "mode": benchmark.mode,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "roles": {
            "reviewer": _spec_to_json(benchmark.roles.reviewer),
            "reviewer_a": _spec_to_json(benchmark.roles.reviewer_a),
            "reviewer_b": _spec_to_json(benchmark.roles.reviewer_b),
            "self_checker": _spec_to_json(benchmark.roles.self_checker),
            "adjudicator": _spec_to_json(benchmark.roles.adjudicator),
        },
        "aggregate": {
            "cases": len(benchmark.cases),
            "machine_refuted": sum(item.machine_refuted for item in benchmark.cases),
            "machine_verified": sum(item.machine_verified for item in benchmark.cases),
            "llm_suspected": sum(item.llm_suspected for item in benchmark.cases),
            "needs_human_check": sum(item.needs_human_check for item in benchmark.cases),
            "llm_provider_reviews": sum(item.llm_provider_reviews for item in benchmark.cases),
            "llm_self_checks": sum(item.llm_self_checks for item in benchmark.cases),
            "llm_adjudications": sum(item.llm_adjudications for item in benchmark.cases),
            "passed": sum(1 for item in benchmark.cases if item.passed is True),
            "failed": sum(1 for item in benchmark.cases if item.passed is False),
            "not_scored": sum(1 for item in benchmark.cases if item.passed is None),
        },
        "suite_metrics": suite_metrics,
        "cases": [
            {
                "case_id": item.case_id,
                "source": str(item.source),
                "run_dir": str(item.run_dir),
                "machine_refuted": item.machine_refuted,
                "machine_verified": item.machine_verified,
                "llm_suspected": item.llm_suspected,
                "needs_human_check": item.needs_human_check,
                "blueprints": item.blueprints,
                "llm_provider_reviews": item.llm_provider_reviews,
                "llm_self_checks": item.llm_self_checks,
                "llm_adjudications": item.llm_adjudications,
                "warnings": item.warnings,
                "passed": item.passed,
                "pass_message": item.pass_message,
                "metadata": item.metadata,
            }
            for item in benchmark.cases
        ],
    }
    (benchmark.report_dir / "benchmark_summary.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )
    (benchmark.report_dir / "benchmark_summary.md").write_text(
        _render_benchmark_summary(payload),
        encoding="utf-8",
    )


def _render_benchmark_summary(payload: dict[str, object]) -> str:
    aggregate = payload["aggregate"]
    roles = payload["roles"]
    lines = [
        "# ReviseAgent Benchmark",
        "",
        f"- Suite: `{payload['suite']}`",
        f"- Mode: `{payload['mode']}`",
        f"- Reviewer: `{_render_role_label(roles['reviewer'])}`",
        f"- Reviewer A: `{_render_role_label(roles['reviewer_a'])}`",
        f"- Reviewer B: `{_render_role_label(roles['reviewer_b'])}`",
        f"- Self-checker: `{_render_role_label(roles['self_checker'])}`",
        f"- Adjudicator: `{_render_role_label(roles['adjudicator'])}`",
        f"- Cases: `{aggregate['cases']}`",
        f"- Machine refuted: `{aggregate['machine_refuted']}`",
        f"- Machine verified: `{aggregate['machine_verified']}`",
        f"- LLM-suspected: `{aggregate['llm_suspected']}`",
        f"- Needs human check: `{aggregate['needs_human_check']}`",
        f"- LLM provider reviews: `{aggregate['llm_provider_reviews']}`",
        f"- LLM self-checks: `{aggregate['llm_self_checks']}`",
        f"- LLM adjudications: `{aggregate['llm_adjudications']}`",
        f"- Passed: `{aggregate['passed']}`",
        f"- Failed: `{aggregate['failed']}`",
        f"- Not scored: `{aggregate['not_scored']}`",
        "",
    ]
    suite_metrics = payload.get("suite_metrics", {})
    if suite_metrics:
        lines.extend(["## Suite Metrics", ""])
        for key, value in suite_metrics.items():
            lines.append(f"- {key}: `{value}`")
        lines.append("")
    lines.extend(["## Cases", ""])
    for item in payload["cases"]:
        score = "not-scored" if item["passed"] is None else ("PASS" if item["passed"] else "FAIL")
        lines.append(
            f"- `{item['case_id']}`: {score}, "
            f"refuted={item['machine_refuted']}, verified={item['machine_verified']}, "
            f"llm_suspected={item['llm_suspected']}, needs_human_check={item['needs_human_check']}, "
            f"self_checks={item['llm_self_checks']}, adjudications={item['llm_adjudications']} "
            f"(`{item['run_dir']}`)"
        )
        metadata = item.get("metadata", {})
        if metadata.get("expert_rating") is not None:
            lines.append(f"  expert_rating={metadata['expert_rating']}")
        if metadata.get("label") is not None:
            lines.append(
                f"  expected_first_issue_step={metadata['label']}, final_answer_correct={metadata.get('final_answer_correct')}"
            )
        if item["pass_message"] and item["pass_message"] != "ok":
            lines.append(f"  note: {item['pass_message']}")
    return "\n".join(lines) + "\n"


def _compute_suite_metrics(benchmark: BenchmarkRun) -> dict[str, object]:
    computer = _SUITE_METRIC_COMPUTERS.get(benchmark.suite, _compute_default_suite_metrics)
    return computer(benchmark)


def _slugify_case_id(case_id: str) -> str:
    return "".join(char if char.isalnum() else "_" for char in case_id).strip("_")[:120] or "case"


def _spec_to_json(spec: ProviderModelSpec | None) -> dict[str, str] | None:
    if spec is None:
        return None
    return {"provider": spec.provider, "model": spec.model or ""}


def _render_role_label(value: dict[str, str] | None) -> str:
    if value is None:
        return "none"
    if value["model"]:
        return f"{value['provider']}:{value['model']}"
    return value["provider"]


def _run_deterministic_only(roles: BenchmarkRoles) -> dict[str, object]:
    del roles
    return {
        "deterministic_checks": True,
        "llm_proof_review": False,
    }


def _run_single_agent(roles: BenchmarkRoles) -> dict[str, object]:
    return {
        "deterministic_checks": False,
        "llm_proof_review": True,
        "proof_review_mode": "single-agent",
        "reviewer_specs": [roles.reviewer],
    }


def _run_single_agent_self_check(roles: BenchmarkRoles) -> dict[str, object]:
    return {
        "deterministic_checks": False,
        "llm_proof_review": True,
        "proof_review_mode": "single-agent-self-check",
        "reviewer_specs": [roles.reviewer],
        "self_check_spec": roles.self_checker,
    }


def _run_multi_agent_cross_check(roles: BenchmarkRoles) -> dict[str, object]:
    return {
        "deterministic_checks": False,
        "llm_proof_review": True,
        "proof_review_mode": "multi-agent-cross-check",
        "reviewer_specs": [roles.reviewer_a, roles.reviewer_b],
        "adjudicator_spec": roles.adjudicator,
    }


def _run_hybrid_single(roles: BenchmarkRoles) -> dict[str, object]:
    return {
        "deterministic_checks": True,
        "llm_proof_review": True,
        "proof_review_mode": "single-agent",
        "reviewer_specs": [roles.reviewer],
    }


def _run_hybrid_cross(roles: BenchmarkRoles) -> dict[str, object]:
    return {
        "deterministic_checks": True,
        "llm_proof_review": True,
        "proof_review_mode": "multi-agent-cross-check",
        "reviewer_specs": [roles.reviewer_a, roles.reviewer_b],
        "adjudicator_spec": roles.adjudicator,
    }


def _compute_proofbench_suite_metrics(benchmark: BenchmarkRun) -> dict[str, object]:
    scored = [
        (
            int(item.metadata["expert_rating"]),
            item.machine_refuted * 2 + item.llm_suspected * 2 + item.needs_human_check,
        )
        for item in benchmark.cases
        if item.metadata.get("expert_rating") is not None
    ]
    if not scored:
        return {}
    average_issue_score = sum(issue_score for _, issue_score in scored) / len(scored)
    low_bucket = [issue_score for rating, issue_score in scored if rating <= 2]
    high_bucket = [issue_score for rating, issue_score in scored if rating >= 6]
    metrics: dict[str, object] = {
        "average_issue_score": round(average_issue_score, 3),
    }
    if low_bucket:
        metrics["avg_issue_score_rating_le_2"] = round(sum(low_bucket) / len(low_bucket), 3)
    if high_bucket:
        metrics["avg_issue_score_rating_ge_6"] = round(sum(high_bucket) / len(high_bucket), 3)
    return metrics


def _compute_processbench_suite_metrics(benchmark: BenchmarkRun) -> dict[str, object]:
    scored_cases = [item for item in benchmark.cases if item.passed is not None]
    if not scored_cases:
        return {}
    exact = sum(1 for item in scored_cases if item.passed)
    return {
        "exact_first_error_accuracy": round(exact / len(scored_cases), 3),
    }


def _compute_default_suite_metrics(benchmark: BenchmarkRun) -> dict[str, object]:
    del benchmark
    return {}


_SUITE_LOADERS = {
    "math-cases": _load_math_suite_cases,
    "proofnet": _load_proofnet_suite_cases,
    "proofbench": _load_proofbench_suite_cases,
    "processbench": _load_processbench_suite_cases,
    "all": _load_all_suite_cases,
}


_MODE_RUNNERS = {
    "deterministic-only": _run_deterministic_only,
    "single-agent": _run_single_agent,
    "single-agent-self-check": _run_single_agent_self_check,
    "multi-agent-cross-check": _run_multi_agent_cross_check,
    "hybrid-single": _run_hybrid_single,
    "hybrid-cross": _run_hybrid_cross,
}


_SUITE_METRIC_COMPUTERS = {
    "proofbench": _compute_proofbench_suite_metrics,
    "processbench": _compute_processbench_suite_metrics,
}
