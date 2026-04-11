"""Benchmark Revisica against Refine.ink expected findings.

Each refine case contains a markdown paper and a JSON file with expected
comments (title, quote, message, score).  This module runs our full
writing-review pipeline on each paper, then evaluates recall: how many
of Refine.ink's expected findings did we catch?

Matching strategy (two tiers):
1. **Heuristic** — keyword/quote overlap between expected comments and
   our findings.  Fast, deterministic, no LLM cost.
2. **LLM judge** (optional) — an LLM evaluates whether each expected
   comment is semantically covered by our findings.  More accurate but
   adds cost.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime
import json
from pathlib import Path
import re

from ..adjudication_policy import pick_preferred_provider
from ..agents import get_agent, to_agent_spec
from .provenance import (
    RegistryEntry,
    append_to_registry,
    build_provenance,
)
from ..bootstrap import detect_platforms
from ..core_types import AgentSpec, ProviderModelSpec, ReviewResult
from ..model_router import resolve_model_for_task, TASK_WRITING_JUDGE
from ..review import _run_provider_agent
from ..writing_review import (
    WritingReviewRun,
    review_writing_file,
    _extract_findings_payload,
)


# ── data structures ──────────────────────────────────────────────────


@dataclass
class RefineComment:
    """A single expected finding from Refine.ink."""
    id: str
    title: str
    paragraph: str
    quote: str
    message: str
    score: float


@dataclass
class MatchResult:
    """How well an expected comment was matched by our findings."""
    comment: RefineComment
    status: str  # "matched", "partial", "missed"
    matched_findings: list[dict[str, object]]
    confidence: float  # 0.0–1.0
    explanation: str


@dataclass
class RefineCaseResult:
    """Result of benchmarking one refine case."""
    case_id: str
    paper_path: Path
    run: WritingReviewRun | None
    expected_comments: list[RefineComment]
    matches: list[MatchResult]
    our_total_findings: int
    recall: float  # fraction of expected comments matched or partially matched
    full_recall: float  # fraction matched (not partial)
    warnings: list[str]


@dataclass
class RefineBenchmarkRun:
    """Result of the full refine benchmark suite."""
    manifest_path: Path
    report_dir: Path
    cases: list[RefineCaseResult]
    aggregate_recall: float
    aggregate_full_recall: float


# ── public API ───────────────────────────────────────────────────────


def run_refine_benchmark(
    manifest_path: str = "benchmarks/refine/manifest.json",
    output_dir: str | None = None,
    venue_profile: str = "general-academic",
    reviewer_specs: list[ProviderModelSpec] | None = None,
    judge_spec: ProviderModelSpec | None = None,
    use_llm_judge: bool = False,
    llm_judge_spec: ProviderModelSpec | None = None,
    force_bootstrap: bool = False,
    timeout_seconds: int = 300,
) -> RefineBenchmarkRun:
    """Run the refine benchmark suite.

    Parameters
    ----------
    manifest_path : path to the refine manifest.json
    output_dir : override output directory
    venue_profile : venue profile for writing review
    reviewer_specs : provider specs for writing reviewers
    judge_spec : provider spec for the writing judge
    use_llm_judge : if True, use an LLM to evaluate matches (more accurate)
    llm_judge_spec : provider spec for the LLM judge evaluator
    force_bootstrap : force re-bootstrap of platform assets
    timeout_seconds : per-provider timeout (higher default for longer papers)
    """
    manifest_file = Path(manifest_path).expanduser().resolve()
    if not manifest_file.exists():
        raise FileNotFoundError(f"Manifest not found: {manifest_file}")

    base_dir = manifest_file.parent
    payload = json.loads(manifest_file.read_text(encoding="utf-8"))
    report_dir = _make_report_dir(base_dir, output_dir)

    cases: list[RefineCaseResult] = []

    for case_spec in payload["cases"]:
        case_id = case_spec["id"]
        paper_path = base_dir / case_spec["file"]
        data_path = base_dir / case_spec["data_file"]

        # Load expected comments
        data = json.loads(data_path.read_text(encoding="utf-8"))
        expected_comments = _parse_comments(data.get("comments", []))

        # Run our pipeline
        warnings: list[str] = []
        run: WritingReviewRun | None = None
        try:
            run = review_writing_file(
                file_path=str(paper_path),
                output_dir=str(report_dir / case_id / "review"),
                venue_profile=venue_profile,
                reviewer_specs=reviewer_specs,
                judge_spec=judge_spec,
                force_bootstrap=force_bootstrap,
                timeout_seconds=timeout_seconds,
            )
        except Exception as exc:
            warnings.append(f"Pipeline failed for {case_id}: {exc}")

        # Collect our findings
        our_findings = _collect_all_findings(run) if run else []

        # Evaluate matches
        if use_llm_judge and run:
            matches = _evaluate_with_llm_judge(
                expected_comments=expected_comments,
                our_findings=our_findings,
                paper_path=paper_path,
                llm_judge_spec=llm_judge_spec,
                timeout_seconds=timeout_seconds,
                warnings=warnings,
            )
        else:
            matches = _evaluate_heuristic(expected_comments, our_findings)

        matched_count = sum(1 for m in matches if m.status in ("matched", "partial"))
        full_matched = sum(1 for m in matches if m.status == "matched")
        total_expected = len(expected_comments)
        recall = matched_count / total_expected if total_expected > 0 else 1.0
        full_recall = full_matched / total_expected if total_expected > 0 else 1.0

        result = RefineCaseResult(
            case_id=case_id,
            paper_path=paper_path,
            run=run,
            expected_comments=expected_comments,
            matches=matches,
            our_total_findings=len(our_findings),
            recall=recall,
            full_recall=full_recall,
            warnings=warnings,
        )
        cases.append(result)
        _write_case_report(report_dir / case_id, result)

    # Aggregate
    total_expected = sum(len(c.expected_comments) for c in cases)
    total_matched = sum(
        sum(1 for m in c.matches if m.status in ("matched", "partial"))
        for c in cases
    )
    total_full = sum(
        sum(1 for m in c.matches if m.status == "matched")
        for c in cases
    )
    aggregate_recall = total_matched / total_expected if total_expected > 0 else 1.0
    aggregate_full_recall = total_full / total_expected if total_expected > 0 else 1.0

    run_result = RefineBenchmarkRun(
        manifest_path=manifest_file,
        report_dir=report_dir,
        cases=cases,
        aggregate_recall=aggregate_recall,
        aggregate_full_recall=aggregate_full_recall,
    )
    _write_benchmark_summary(report_dir, run_result)

    # Registry
    provenance = build_provenance(
        suite="refine",
        extra={"venue_profile": venue_profile, "use_llm_judge": use_llm_judge},
    )
    entry = RegistryEntry(
        provenance=provenance,
        passed=total_full,
        total=total_expected,
        case_results=[
            {
                "case_id": c.case_id,
                "recall": c.recall,
                "full_recall": c.full_recall,
                "our_findings": c.our_total_findings,
                "expected": len(c.expected_comments),
            }
            for c in cases
        ],
        report_dir=str(report_dir),
    )
    append_to_registry(entry)

    return run_result


# ── comment parsing ──────────────────────────────────────────────────


def _parse_comments(raw_comments: list[dict[str, object]]) -> list[RefineComment]:
    comments = []
    for raw in raw_comments:
        comments.append(
            RefineComment(
                id=str(raw.get("id", "")),
                title=str(raw.get("title", "")),
                paragraph=str(raw.get("paragraph", "")),
                quote=str(raw.get("quote", "")),
                message=str(raw.get("message", "")),
                score=float(raw.get("score", 0.0)),
            )
        )
    return comments


# ── finding collection ───────────────────────────────────────────────


def _collect_all_findings(run: WritingReviewRun) -> list[dict[str, object]]:
    findings: list[dict[str, object]] = []
    for artifact in run.artifacts:
        if artifact.findings is not None:
            for f in artifact.findings:
                enriched = dict(f)
                enriched["_role"] = artifact.role
                enriched["_provider"] = artifact.provider
                findings.append(enriched)
    return findings


# ── heuristic matching ───────────────────────────────────────────────


def _normalize_text(text: str) -> str:
    """Lowercase, strip, collapse whitespace, remove LaTeX commands."""
    text = text.lower()
    text = re.sub(r"\\[a-zA-Z]+\{([^}]*)\}", r"\1", text)  # \cmd{arg} → arg
    text = re.sub(r"[\$\\{}]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _extract_keywords(text: str) -> set[str]:
    """Extract meaningful keywords (3+ chars) from normalized text."""
    normalized = _normalize_text(text)
    words = set(normalized.split())
    # Filter stopwords and short words
    stopwords = {
        "the", "and", "for", "that", "this", "with", "from", "are", "was",
        "were", "been", "have", "has", "had", "not", "but", "its", "also",
        "can", "may", "will", "would", "should", "could", "each", "which",
        "than", "then", "when", "where", "how", "all", "any", "both",
    }
    return {w for w in words if len(w) >= 3 and w not in stopwords}


def _compute_overlap(text_a: str, text_b: str) -> float:
    """Compute keyword overlap ratio between two texts."""
    kw_a = _extract_keywords(text_a)
    kw_b = _extract_keywords(text_b)
    if not kw_a or not kw_b:
        return 0.0
    intersection = kw_a & kw_b
    # Jaccard-like but weighted toward smaller set (the expected comment)
    return len(intersection) / min(len(kw_a), len(kw_b))


def _evaluate_heuristic(
    expected: list[RefineComment],
    our_findings: list[dict[str, object]],
) -> list[MatchResult]:
    """Evaluate matches using keyword/quote overlap heuristics."""
    results: list[MatchResult] = []

    for comment in expected:
        # Build a combined text from the expected comment
        expected_text = f"{comment.title} {comment.quote} {comment.message}"

        best_score = 0.0
        best_findings: list[dict[str, object]] = []

        for finding in our_findings:
            # Build finding text from all available fields
            parts = []
            for key in ("title", "snippet", "explanation", "fix", "category"):
                val = finding.get(key)
                if val:
                    parts.append(str(val))
            finding_text = " ".join(parts)

            # Score: weighted combination of title overlap and full-text overlap
            title_overlap = _compute_overlap(comment.title, finding_text)
            quote_overlap = _compute_overlap(comment.quote, finding_text)
            full_overlap = _compute_overlap(expected_text, finding_text)

            score = max(
                title_overlap * 0.6 + full_overlap * 0.4,
                quote_overlap * 0.5 + full_overlap * 0.5,
                full_overlap,
            )

            if score > 0.25:  # threshold for "possible match"
                best_findings.append(finding)
                best_score = max(best_score, score)

        if best_score >= 0.45:
            status = "matched"
        elif best_score >= 0.25:
            status = "partial"
        else:
            status = "missed"

        results.append(
            MatchResult(
                comment=comment,
                status=status,
                matched_findings=best_findings[:3],  # top 3
                confidence=best_score,
                explanation=f"Heuristic score: {best_score:.2f}",
            )
        )

    return results


def _evaluate_with_llm_judge(
    expected_comments: list[RefineComment],
    our_findings: list[dict[str, object]],
    paper_path: Path,
    llm_judge_spec: ProviderModelSpec | None,
    timeout_seconds: int,
    warnings: list[str],
) -> list[MatchResult]:
    """Use an LLM to evaluate which expected comments are covered by our findings.

    Falls back to heuristic matching if LLM judge fails.
    """
    platforms = detect_platforms()

    # Resolve judge spec
    if llm_judge_spec is None:
        available = [
            name for name, p in platforms.items() if p.available
        ]
        if not available:
            warnings.append("No provider available for LLM judge; falling back to heuristic matching.")
            return _evaluate_heuristic(expected_comments, our_findings)
        llm_judge_spec = ProviderModelSpec(provider=pick_preferred_provider(available))

    llm_judge_spec = resolve_model_for_task(llm_judge_spec, TASK_WRITING_JUDGE)

    if not platforms.get(llm_judge_spec.provider, None) or not platforms[llm_judge_spec.provider].available:
        warnings.append(f"LLM judge provider '{llm_judge_spec.provider}' not available; falling back to heuristic.")
        return _evaluate_heuristic(expected_comments, our_findings)

    platform = platforms[llm_judge_spec.provider]

    # Build the evaluation prompt
    expected_json = json.dumps(
        [
            {
                "id": c.id,
                "title": c.title,
                "quote": c.quote[:300],
                "message": c.message[:500],
            }
            for c in expected_comments
        ],
        indent=2,
        ensure_ascii=False,
    )

    # Compact findings representation
    findings_json = json.dumps(
        [
            {
                "idx": i,
                "role": f.get("_role", "unknown"),
                "category": f.get("category", ""),
                "title": f.get("title", ""),
                "snippet": str(f.get("snippet", ""))[:200],
                "explanation": str(f.get("explanation", ""))[:300],
            }
            for i, f in enumerate(our_findings)
        ],
        indent=2,
        ensure_ascii=False,
    )

    task_prompt = (
        f"You are evaluating how well a set of review findings covers expected issues.\n\n"
        f"The paper is at: `{paper_path}`\n\n"
        f"## Expected issues (from a reference reviewer):\n```json\n{expected_json}\n```\n\n"
        f"## Actual findings (from our review system):\n```json\n{findings_json}\n```\n\n"
        f"For EACH expected issue, determine whether any actual finding(s) cover it.\n"
        f"A finding covers an issue if it identifies the same underlying problem, "
        f"even with different wording.\n\n"
        f"Return JSON with this schema:\n"
        f'{{"evaluations": [\n'
        f'  {{"id": "comment-1", "status": "matched"|"partial"|"missed", '
        f'"matched_finding_indices": [0, 3], "confidence": 0.85, '
        f'"explanation": "Finding #0 identifies the same sign error..."}}\n'
        f"]}}"
    )

    agent_spec = to_agent_spec(get_agent("refine-eval-judge"))

    try:
        result = _run_provider_agent(
            llm_judge_spec.provider,
            task_prompt,
            agent_spec,
            timeout_seconds,
            model=llm_judge_spec.model,
            working_dir=str(paper_path.parent),
        )
    except Exception as exc:
        warnings.append(f"LLM judge call failed: {exc}; falling back to heuristic.")
        return _evaluate_heuristic(expected_comments, our_findings)

    if not result.success:
        warnings.append("LLM judge returned non-success; falling back to heuristic.")
        return _evaluate_heuristic(expected_comments, our_findings)

    # Parse LLM judge output
    evaluations = _parse_judge_output(result.output)
    if evaluations is None:
        warnings.append("Could not parse LLM judge output; falling back to heuristic.")
        return _evaluate_heuristic(expected_comments, our_findings)

    # Build MatchResults from LLM evaluations
    comment_by_id = {c.id: c for c in expected_comments}
    results: list[MatchResult] = []

    for ev in evaluations:
        comment_id = ev.get("id", "")
        comment = comment_by_id.get(comment_id)
        if comment is None:
            continue
        status = ev.get("status", "missed")
        if status not in ("matched", "partial", "missed"):
            status = "missed"
        indices = ev.get("matched_finding_indices", [])
        matched = [our_findings[i] for i in indices if 0 <= i < len(our_findings)]
        confidence = float(ev.get("confidence", 0.0))
        explanation = str(ev.get("explanation", ""))

        results.append(
            MatchResult(
                comment=comment,
                status=status,
                matched_findings=matched[:3],
                confidence=confidence,
                explanation=f"LLM judge: {explanation}",
            )
        )

    # Fill in any expected comments not covered by judge output
    evaluated_ids = {m.comment.id for m in results}
    for comment in expected_comments:
        if comment.id not in evaluated_ids:
            results.append(
                MatchResult(
                    comment=comment,
                    status="missed",
                    matched_findings=[],
                    confidence=0.0,
                    explanation="Not evaluated by LLM judge",
                )
            )

    return results


def _parse_judge_output(output: str) -> list[dict[str, object]] | None:
    """Parse the LLM judge's JSON output."""
    text = output.strip()
    if not text:
        return None

    # Try direct parse
    try:
        data = json.loads(text)
        if isinstance(data, dict) and "evaluations" in data:
            return data["evaluations"]
    except json.JSONDecodeError:
        pass

    # Try fenced code block
    for match in re.finditer(r"```(?:json)?\s*\n(.*?)```", text, re.DOTALL):
        try:
            data = json.loads(match.group(1).strip())
            if isinstance(data, dict) and "evaluations" in data:
                return data["evaluations"]
        except json.JSONDecodeError:
            continue

    # Try scanning for {"evaluations"
    start = text.find('"evaluations"')
    if start != -1:
        brace_start = text.rfind("{", 0, start)
        if brace_start != -1:
            depth = 0
            for i in range(brace_start, len(text)):
                if text[i] == "{":
                    depth += 1
                elif text[i] == "}":
                    depth -= 1
                    if depth == 0:
                        try:
                            data = json.loads(text[brace_start : i + 1])
                            if "evaluations" in data:
                                return data["evaluations"]
                        except json.JSONDecodeError:
                            pass
                        break

    return None


# ── reporting ────────────────────────────────────────────────────────


def _make_report_dir(base_dir: Path, output_dir: str | None) -> Path:
    if output_dir:
        report_dir = Path(output_dir).expanduser().resolve()
    else:
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        report_dir = base_dir / "runs" / f"refine-{stamp}"
    report_dir.mkdir(parents=True, exist_ok=True)
    return report_dir


def _write_case_report(case_dir: Path, result: RefineCaseResult) -> None:
    case_dir.mkdir(parents=True, exist_ok=True)

    lines = [
        f"# Refine Benchmark: {result.case_id}",
        "",
        f"- Paper: `{result.paper_path}`",
        f"- Expected comments: {len(result.expected_comments)}",
        f"- Our findings: {result.our_total_findings}",
        f"- Recall (matched + partial): {result.recall:.1%}",
        f"- Full recall (matched only): {result.full_recall:.1%}",
        "",
    ]

    if result.warnings:
        lines.append("## Warnings")
        lines.append("")
        for w in result.warnings:
            lines.append(f"- {w}")
        lines.append("")

    lines.append("## Expected vs Found")
    lines.append("")

    for match in result.matches:
        icon = {"matched": "+", "partial": "~", "missed": "X"}[match.status]
        status_label = {"matched": "MATCHED", "partial": "PARTIAL", "missed": "MISSED"}[match.status]
        lines.append(f"### [{icon}] {status_label}: {match.comment.title}")
        lines.append("")
        lines.append(f"- **Refine score:** {match.comment.score}")
        lines.append(f"- **Match confidence:** {match.confidence:.2f}")
        lines.append(f"- **Explanation:** {match.explanation}")
        if match.comment.quote:
            quote_preview = match.comment.quote[:200]
            lines.append(f"- **Expected quote:** {quote_preview}...")
        if match.matched_findings:
            lines.append(f"- **Matched findings ({len(match.matched_findings)}):**")
            for f in match.matched_findings:
                ftitle = f.get("title", "untitled")
                frole = f.get("_role", "?")
                lines.append(f"  - [{frole}] {ftitle}")
        lines.append("")

    (case_dir / "evaluation.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    # JSON report
    json_report = {
        "case_id": result.case_id,
        "paper_path": str(result.paper_path),
        "expected_comments": len(result.expected_comments),
        "our_total_findings": result.our_total_findings,
        "recall": result.recall,
        "full_recall": result.full_recall,
        "matches": [
            {
                "comment_id": m.comment.id,
                "comment_title": m.comment.title,
                "status": m.status,
                "confidence": m.confidence,
                "explanation": m.explanation,
                "matched_finding_count": len(m.matched_findings),
            }
            for m in result.matches
        ],
        "warnings": result.warnings,
    }
    (case_dir / "evaluation.json").write_text(
        json.dumps(json_report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _write_benchmark_summary(report_dir: Path, run: RefineBenchmarkRun) -> None:
    lines = [
        "# Revisica vs Refine.ink Benchmark",
        "",
        f"- Manifest: `{run.manifest_path}`",
        f"- Report dir: `{run.report_dir}`",
        f"- Cases: {len(run.cases)}",
        f"- **Aggregate recall (matched + partial):** {run.aggregate_recall:.1%}",
        f"- **Aggregate full recall (matched only):** {run.aggregate_full_recall:.1%}",
        "",
        "## Per-Case Results",
        "",
        "| Case | Expected | Found | Recall | Full Recall |",
        "|------|----------|-------|--------|-------------|",
    ]
    for c in run.cases:
        lines.append(
            f"| {c.case_id} | {len(c.expected_comments)} | {c.our_total_findings} | "
            f"{c.recall:.1%} | {c.full_recall:.1%} |"
        )

    lines.extend(["", "## Detailed Match Breakdown", ""])
    for c in run.cases:
        matched = sum(1 for m in c.matches if m.status == "matched")
        partial = sum(1 for m in c.matches if m.status == "partial")
        missed = sum(1 for m in c.matches if m.status == "missed")
        lines.append(f"### {c.case_id}")
        lines.append(f"- Matched: {matched}, Partial: {partial}, Missed: {missed}")
        for m in c.matches:
            icon = {"matched": "+", "partial": "~", "missed": "X"}[m.status]
            lines.append(f"  - [{icon}] {m.comment.title} (conf={m.confidence:.2f})")
        lines.append("")

    (report_dir / "benchmark_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    summary_json = {
        "manifest": str(run.manifest_path),
        "aggregate_recall": run.aggregate_recall,
        "aggregate_full_recall": run.aggregate_full_recall,
        "cases": [
            {
                "case_id": c.case_id,
                "expected": len(c.expected_comments),
                "found": c.our_total_findings,
                "recall": c.recall,
                "full_recall": c.full_recall,
                "matched": sum(1 for m in c.matches if m.status == "matched"),
                "partial": sum(1 for m in c.matches if m.status == "partial"),
                "missed": sum(1 for m in c.matches if m.status == "missed"),
            }
            for c in run.cases
        ],
    }
    (report_dir / "benchmark_summary.json").write_text(
        json.dumps(summary_json, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
