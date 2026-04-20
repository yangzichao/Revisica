from __future__ import annotations

import argparse
from pathlib import Path

from .bootstrap import bootstrap
from .core_types import ProviderModelSpec
from .eval import (
    parse_provider_model_spec,
    render_history,
    run_benchmark,
    run_math_benchmark,
    run_refine_benchmark,
    run_writing_benchmark,
    write_history_report,
)
from .eval.proofnet_adapter import benchmark_proofnet, import_proofnet_cases
from .ingestion import parse_document
from .math_review import review_math_file
from .profiles import ReviewMode
from .templates import SUPPORTED_VENUE_PROFILES
from .unified_review import review_unified
from .writing_review import review_writing_file


# ── helpers ──────────────────────────────────────────────────────────


def _parse_reviewer_specs(args: argparse.Namespace) -> list[ProviderModelSpec] | None:
    """Parse --reviewer-a / --reviewer-b into a spec list (or None)."""
    specs = [
        spec
        for spec in (
            parse_provider_model_spec(getattr(args, "reviewer_a", None)),
            parse_provider_model_spec(getattr(args, "reviewer_b", None)),
        )
        if spec is not None
    ]
    return specs or None


# ── parser construction ──────────────────────────────────────────────


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="revisica",
        description="Minimal POC for reviewing LaTeX drafts with Codex and Claude.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    _add_bootstrap_parser(sub)
    _add_serve_parser(sub)
    _add_ingest_parser(sub)
    _add_review_parser(sub)
    _add_writing_review_parser(sub)
    _add_math_review_parser(sub)
    _add_benchmark_math_parser(sub)
    _add_benchmark_writing_parser(sub)
    _add_benchmark_history_parser(sub)
    _add_import_proofnet_parser(sub)
    _add_benchmark_proofnet_parser(sub)
    _add_benchmark_run_parser(sub)
    _add_benchmark_refine_parser(sub)
    _add_benchmark_ingestion_parser(sub)

    return parser


def _add_bootstrap_parser(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("bootstrap", help="Install local review assets.")
    p.add_argument("--targets", nargs="+", choices=["codex", "claude"],
                   help="Specific provider targets to bootstrap.")
    p.add_argument("--force", action="store_true",
                   help="Overwrite existing installed assets.")


def _add_serve_parser(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("serve",
                       help="Start the Revisica API server (for desktop app).")
    p.add_argument("--host", default="127.0.0.1",
                   help="Host to bind to (default: 127.0.0.1).")
    p.add_argument("--port", type=int, default=18321,
                   help="Port to listen on (default: 18321).")


def _add_ingest_parser(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("ingest",
                       help="Parse a PDF or .tex file into a RevisicaDocument.")
    p.add_argument("file", help="Path to the input file (PDF or .tex).")
    p.add_argument("--parser", default="auto",
                   choices=["auto", "mathpix", "mineru", "marker", "pandoc", "tex-basic"],
                   help="Parser to use (default: auto-detect).")
    p.add_argument("--output",
                   help="Write the RevisicaDocument JSON to a file instead of stdout.")


def _add_review_parser(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("review",
                       help="Run unified review: writing + math lanes concurrently.")
    p.add_argument("file", help="Path to the target paper (PDF or .tex).")
    p.add_argument("--mode", default="review",
                   choices=["polish", "review"],
                   help="Review mode: 'polish' for writing-only, 'review' for full deep analysis.")
    p.add_argument("--output-dir",
                   help="Directory where the unified run artifacts should be written.")
    p.add_argument("--venue-profile", default="general-academic",
                   choices=list(SUPPORTED_VENUE_PROFILES),
                   help="Target venue/style profile for the writing lane.")
    p.add_argument("--reviewer-a",
                   help="Primary writing reviewer spec formatted as provider[:model].")
    p.add_argument("--reviewer-b",
                   help="Secondary writing reviewer spec formatted as provider[:model].")
    p.add_argument("--judge",
                   help="Writing judge/adjudicator spec formatted as provider[:model].")
    p.add_argument("--llm-proof-review", action="store_true",
                   help="Use available providers to review extracted proof obligations (math lane).")
    p.add_argument("--targets", nargs="+", choices=["codex", "claude"],
                   help="Specific providers for math-lane LLM proof review.")
    p.add_argument("--force-bootstrap", action="store_true",
                   help="Overwrite existing platform assets when auto-bootstrapping.")
    p.add_argument("--timeout-seconds", type=int, default=120,
                   help="Per-provider timeout in seconds.")
    _add_codex_reasoning_flag(p)


def _add_writing_review_parser(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("writing-review", help="Run a multi-agent writing review.")
    p.add_argument("file", help="Path to the target LaTeX draft.")
    p.add_argument("--output-dir",
                   help="Directory where the writing review artifacts should be written.")
    p.add_argument("--venue-profile", default="general-academic",
                   choices=list(SUPPORTED_VENUE_PROFILES),
                   help="Target venue/style profile.")
    p.add_argument("--reviewer-a",
                   help="Primary reviewer spec formatted as provider[:model].")
    p.add_argument("--reviewer-b",
                   help="Secondary reviewer spec formatted as provider[:model].")
    p.add_argument("--judge",
                   help="Judge/adjudicator spec formatted as provider[:model].")
    p.add_argument("--force-bootstrap", action="store_true",
                   help="Overwrite existing platform assets when auto-bootstrapping.")
    p.add_argument("--timeout-seconds", type=int, default=120,
                   help="Per-provider timeout for writing-review LLM calls.")
    _add_codex_reasoning_flag(p)


def _add_math_review_parser(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("math-review",
                       help="Run deterministic math checks on a LaTeX file.")
    p.add_argument("file", help="Path to the target LaTeX draft.")
    p.add_argument("--output-dir",
                   help="Directory where the math review artifacts should be written.")
    p.add_argument("--llm-proof-review", action="store_true",
                   help="Use available providers to review extracted proof obligations.")
    p.add_argument("--targets", nargs="+", choices=["codex", "claude"],
                   help="Specific providers to use for optional proof-obligation review.")
    p.add_argument("--force-bootstrap", action="store_true",
                   help="Overwrite existing platform assets when auto-bootstrapping.")
    p.add_argument("--timeout-seconds", type=int, default=120,
                   help="Per-provider timeout for optional LLM proof review.")
    _add_codex_reasoning_flag(p)


def _add_codex_reasoning_flag(p: argparse.ArgumentParser) -> None:
    """Shared --codex-reasoning flag for Codex ``model_reasoning_effort``.

    When set, this runtime override wins over any per-agent default (e.g.
    the proof reviewers default to ``xhigh``). When unset, each agent's
    own default applies — or falls back to the user's config.toml.
    """
    p.add_argument(
        "--codex-reasoning",
        choices=["none", "minimal", "low", "medium", "high", "xhigh"],
        help="Override Codex's model_reasoning_effort for this run "
             "(xhigh = max; wins over per-agent defaults).",
    )


def _add_benchmark_math_parser(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("benchmark-math", help="Run the local math benchmark suite.")
    p.add_argument("--manifest", default="benchmarks/math/manifest.json",
                   help="Path to the benchmark manifest JSON.")


def _add_benchmark_writing_parser(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("benchmark-writing",
                       help="Run the local writing benchmark suite.")
    p.add_argument("--manifest", default="benchmarks/writing/manifest.json",
                   help="Path to the writing benchmark manifest JSON.")
    p.add_argument("--venue-profile",
                   help="Override venue profile for all cases.")
    p.add_argument("--force-bootstrap", action="store_true",
                   help="Overwrite existing platform assets when auto-bootstrapping.")
    p.add_argument("--timeout-seconds", type=int, default=120,
                   help="Per-provider timeout for writing benchmark LLM calls.")


def _add_benchmark_history_parser(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("benchmark-history",
                       help="Render benchmark history from the registry.")
    p.add_argument("--suite",
                   help="Filter history to a specific suite (e.g. math, writing).")
    p.add_argument("--limit", type=int,
                   help="Show only the last N runs.")
    p.add_argument("--output",
                   help="Write the history report to a file instead of stdout.")


def _add_import_proofnet_parser(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("import-proofnet",
                       help="Import a small ProofNet slice into local LaTeX benchmark cases.")
    p.add_argument("--split", default="test", choices=["test", "valid"])
    p.add_argument("--limit", type=int, default=10)
    p.add_argument("--output-dir",
                   help="Directory where imported ProofNet cases should be written.")


def _add_benchmark_proofnet_parser(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("benchmark-proofnet",
                       help="Import and run a small ProofNet-based math benchmark.")
    p.add_argument("--split", default="test", choices=["test", "valid"])
    p.add_argument("--limit", type=int, default=10)
    p.add_argument("--output-dir",
                   help="Directory where imported ProofNet cases and benchmark runs should be written.")
    p.add_argument("--llm-proof-review", action="store_true",
                   help="Use available providers to review extracted proof obligations.")
    p.add_argument("--targets", nargs="+", choices=["codex", "claude"],
                   help="Specific providers to use for optional ProofNet proof review.")
    p.add_argument("--force-bootstrap", action="store_true",
                   help="Overwrite existing platform assets when auto-bootstrapping.")
    p.add_argument("--timeout-seconds", type=int, default=120,
                   help="Per-provider timeout for optional ProofNet proof review.")


def _add_benchmark_run_parser(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("benchmark-run",
                       help="Run a unified benchmark suite with explicit mode and role/model selection.")
    p.add_argument("--suite", default="math-cases",
                   choices=["math-cases", "proofnet", "proofbench", "processbench", "prmbench", "asymob", "all"],
                   help="Benchmark suite to run.")
    p.add_argument("--mode", required=True,
                   choices=["deterministic-only", "single-agent", "single-agent-self-check",
                            "multi-agent-cross-check", "hybrid-single", "hybrid-cross"],
                   help="Benchmark orchestration mode.")
    p.add_argument("--manifest",
                   help="Manifest for the local math-cases suite.")
    p.add_argument("--split", default="test",
                   help="Dataset split when relevant.")
    p.add_argument("--limit", type=int, default=10,
                   help="Import limit when suite includes proofnet.")
    p.add_argument("--output-dir",
                   help="Directory where benchmark outputs should be written.")
    p.add_argument("--reviewer", help="Single reviewer role, formatted as provider[:model].")
    p.add_argument("--reviewer-a", help="Reviewer A role, formatted as provider[:model].")
    p.add_argument("--reviewer-b", help="Reviewer B role, formatted as provider[:model].")
    p.add_argument("--self-checker", help="Self-check role, formatted as provider[:model].")
    p.add_argument("--adjudicator", help="Adjudicator role, formatted as provider[:model].")
    p.add_argument("--force-bootstrap", action="store_true",
                   help="Overwrite existing platform assets when auto-bootstrapping.")
    p.add_argument("--timeout-seconds", type=int, default=120,
                   help="Per-provider timeout for benchmark LLM calls.")
    p.add_argument("--agent-version",
                   help="Proof reviewer agent prompt version (e.g. v0, v1). Defaults to latest.")
    p.add_argument("--workers", type=int, default=1,
                   help="Number of cases to run concurrently (default: 1, sequential).")


def _add_benchmark_refine_parser(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("benchmark-refine",
                       help="Benchmark against Refine.ink expected findings.")
    p.add_argument("--manifest", default="benchmarks/refine/manifest.json",
                   help="Path to the refine manifest JSON.")
    p.add_argument("--output-dir",
                   help="Directory where benchmark outputs should be written.")
    p.add_argument("--venue-profile", default="general-academic",
                   choices=list(SUPPORTED_VENUE_PROFILES),
                   help="Target venue/style profile for writing review.")
    p.add_argument("--reviewer-a",
                   help="Primary reviewer spec formatted as provider[:model].")
    p.add_argument("--reviewer-b",
                   help="Secondary reviewer spec formatted as provider[:model].")
    p.add_argument("--judge",
                   help="Writing judge/adjudicator spec formatted as provider[:model].")
    p.add_argument("--use-llm-judge", action="store_true",
                   help="Use an LLM to evaluate matches (more accurate, adds cost).")
    p.add_argument("--llm-judge",
                   help="Provider[:model] for the LLM evaluation judge.")
    p.add_argument("--force-bootstrap", action="store_true",
                   help="Overwrite existing platform assets when auto-bootstrapping.")
    p.add_argument("--timeout-seconds", type=int, default=300,
                   help="Per-provider timeout (default 300s for longer papers).")


def _add_benchmark_ingestion_parser(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser(
        "benchmark-ingestion",
        help="Benchmark PDF/tex parsers (Pandoc, tex-basic, MinerU per-backend, Mathpix) "
             "against arXiv ground truth.",
        description=(
            "Runs every selected parser on the same arXiv corpus and writes a "
            "leaderboard comparing correctness (title/authors/abstract match) "
            "and structural quality (math extraction, clean headings, leftover "
            "LaTeX). First run downloads PDFs from arXiv (~4s/paper throttled) "
            "and fetches ground-truth metadata from the arXiv API."
        ),
    )
    p.add_argument(
        "--parsers", nargs="+", default=["all"],
        help="Parsers to run. Tokens: 'all' (every default parser except "
             "Mathpix), 'mineru' (all three MinerU backends), or explicit "
             "keys like 'pandoc', 'tex-basic', 'mineru:pipeline', 'mineru:vlm', "
             "'mineru:hybrid', 'mathpix'. Mathpix is NOT in 'all' because it "
             "costs money — opt in explicitly."
    )
    p.add_argument(
        "--limit", type=int, default=3,
        help="Number of arXiv papers from the corpus manifest to benchmark. "
             "Default 3 keeps a full MinerU run under ~15 minutes."
    )
    p.add_argument(
        "--paper-id", action="append", default=[],
        help="Specific arxiv id(s) to run (repeatable). Overrides --limit."
    )
    p.add_argument(
        "--fixtures-root",
        default="tests/fixtures/arxiv",
        help="Directory with manifest.json and per-paper subfolders."
    )
    p.add_argument(
        "--ground-truth-dir",
        default="benchmarks/ingestion/ground_truth",
        help="Directory used to cache arXiv API responses."
    )
    p.add_argument(
        "--skip-ground-truth", action="store_true",
        help="Skip arXiv API lookups; only record structural metrics."
    )
    p.add_argument(
        "--no-pdf-download", action="store_true",
        help="Do not fetch missing PDFs from arXiv (useful for offline runs)."
    )
    p.add_argument(
        "--timeout-seconds", type=int, default=900,
        help="Per-parser subprocess timeout. MinerU VLM on MPS often needs "
             "several minutes per paper."
    )
    p.add_argument(
        "--output-dir",
        help="Where to write leaderboard/per_paper/artifacts. Defaults to "
             "benchmarks/ingestion/runs/<timestamp>/."
    )


# ── command handlers ─────────────────────────────────────────────────


def _handle_review(args: argparse.Namespace) -> None:
    run = review_unified(
        file_path=args.file,
        output_dir=args.output_dir,
        venue_profile=args.venue_profile,
        reviewer_specs=_parse_reviewer_specs(args),
        judge_spec=parse_provider_model_spec(args.judge),
        llm_proof_review=args.llm_proof_review,
        targets=args.targets,
        force_bootstrap=args.force_bootstrap,
        timeout_seconds=args.timeout_seconds,
        mode=getattr(args, "mode", "review"),
        codex_reasoning_effort=getattr(args, "codex_reasoning", None),
    )
    print("environment check: unified review (writing + math)")
    print(f"unified artifacts: {run.run_dir}")
    for warning in run.warnings:
        print(f"warning: {warning}")
    if run.writing is not None:
        w = run.writing
        print(f"writing lane: {w.mode}, {len(w.artifacts)} role runs, artifacts at {w.run_dir}")
        if w.final_report is not None:
            state = "ok" if w.final_report.success else "failed"
            print(f"writing final report: {state} ({w.run_dir / 'final_report.md'})")
    else:
        print("writing lane: failed")
    if run.math is not None:
        m = run.math
        refuted = sum(1 for i in m.issues if i.status == "machine-refuted")
        verified = sum(1 for i in m.issues if i.status == "machine-verified")
        print(f"math lane: refuted={refuted}, verified={verified}, blueprints={len(m.blueprints)}")
        print(f"math report: {m.run_dir / 'math_report.md'}")
    else:
        print("math lane: failed")
    print(f"summary: {run.run_dir / 'summary.md'}")


def _handle_writing_review(args: argparse.Namespace) -> None:
    result = review_writing_file(
        file_path=args.file,
        output_dir=args.output_dir,
        venue_profile=args.venue_profile,
        reviewer_specs=_parse_reviewer_specs(args),
        judge_spec=parse_provider_model_spec(args.judge),
        force_bootstrap=args.force_bootstrap,
        timeout_seconds=args.timeout_seconds,
        codex_reasoning_effort=getattr(args, "codex_reasoning", None),
    )
    print("environment check: multi-agent writing review")
    print(f"writing artifacts: {result.run_dir}")
    print(f"venue profile: {result.venue_profile}")
    print(f"mode: {result.mode}")
    print(f"role runs: {len(result.artifacts)}")
    for warning in result.warnings:
        print(f"warning: {warning}")
    if result.final_report is not None:
        label = result.final_report.provider
        if result.final_report.model:
            label = f"{label}:{result.final_report.model}"
        state = "ok" if result.final_report.success else "failed"
        print(f"final report: {state} via {label} ({result.run_dir / 'final_report.md'})")


def _handle_math_review(args: argparse.Namespace) -> None:
    run = review_math_file(
        file_path=args.file,
        output_dir=args.output_dir,
        llm_proof_review=args.llm_proof_review,
        targets=args.targets,
        force_bootstrap=args.force_bootstrap,
        timeout_seconds=args.timeout_seconds,
        codex_reasoning_effort=getattr(args, "codex_reasoning", None),
    )
    refuted = sum(1 for item in run.issues if item.status == "machine-refuted")
    verified = sum(1 for item in run.issues if item.status == "machine-verified")
    llm_suspected = sum(1 for item in run.issues if item.status == "llm-suspected")
    pending = sum(1 for item in run.issues if item.status == "needs-human-check")
    print("environment check: deterministic math pipeline active")
    print(f"math artifacts: {run.run_dir}")
    print(f"functions extracted: {len(run.functions)}")
    print(f"claims extracted: {len(run.claims)}")
    print(f"theorem/proof blueprints: {len(run.blueprints)}")
    print(f"machine-refuted: {refuted}")
    print(f"machine-verified: {verified}")
    print(f"llm-suspected: {llm_suspected}")
    print(f"needs-human-check: {pending}")
    for warning in run.warnings:
        print(f"warning: {warning}")
    for index, artifact in enumerate(run.llm_provider_results, start=1):
        state = "ok" if artifact.result.success else "failed"
        print(
            f"llm-proof-review-{index}-{artifact.provider}-theorem-{artifact.theorem_line_number}: "
            f"{state} (exit={artifact.result.returncode})"
        )
    for index, artifact in enumerate(run.llm_adjudication_results, start=1):
        state = "ok" if artifact.result.success else "failed"
        print(
            f"llm-proof-adjudication-{index}-{artifact.adjudicator_provider}-theorem-{artifact.theorem_line_number}: "
            f"{state} (exit={artifact.result.returncode})"
        )
    print(f"math report: {run.run_dir / 'math_report.md'}")


def _handle_benchmark_math(args: argparse.Namespace) -> None:
    results, report_dir = run_math_benchmark(args.manifest)
    passed = sum(1 for item in results if item.passed)
    print("environment check: local math benchmark suite")
    print(f"benchmark report dir: {report_dir}")
    print(f"passed: {passed}/{len(results)}")
    for item in results:
        status = "PASS" if item.passed else "FAIL"
        print(f"{item.case_id}: {status} - {item.message}")
    print(f"summary: {report_dir / 'benchmark_summary.md'}")


def _handle_benchmark_writing(args: argparse.Namespace) -> None:
    results, report_dir = run_writing_benchmark(
        manifest_path=args.manifest,
        venue_profile=args.venue_profile,
        force_bootstrap=args.force_bootstrap,
        timeout_seconds=args.timeout_seconds,
    )
    passed = sum(1 for item in results if item.passed)
    print("environment check: local writing benchmark suite")
    print(f"benchmark report dir: {report_dir}")
    print(f"passed: {passed}/{len(results)}")
    for item in results:
        status = "PASS" if item.passed else "FAIL"
        print(f"{item.case_id}: {status} - {item.message}")
    print(f"summary: {report_dir / 'benchmark_summary.md'}")


def _handle_benchmark_history(args: argparse.Namespace) -> None:
    output_path = Path(args.output) if args.output else None
    if output_path:
        path = write_history_report(
            output_path=output_path,
            suite_filter=args.suite,
            limit=args.limit,
        )
        print(f"history report: {path}")
    else:
        print(render_history(suite_filter=args.suite, limit=args.limit), end="")


def _handle_benchmark_run(args: argparse.Namespace) -> None:
    result = run_benchmark(
        suite=args.suite,
        mode=args.mode,
        output_dir=args.output_dir,
        manifest=args.manifest,
        split=args.split,
        limit=args.limit,
        reviewer=parse_provider_model_spec(args.reviewer),
        reviewer_a=parse_provider_model_spec(args.reviewer_a),
        reviewer_b=parse_provider_model_spec(args.reviewer_b),
        self_checker=parse_provider_model_spec(args.self_checker),
        adjudicator=parse_provider_model_spec(args.adjudicator),
        force_bootstrap=args.force_bootstrap,
        timeout_seconds=args.timeout_seconds,
        agent_version=getattr(args, "agent_version", None),
        workers=getattr(args, "workers", 1),
    )
    print("environment check: unified benchmark runner")
    print(f"suite: {result.suite}")
    print(f"mode: {result.mode}")
    if result.agent_version:
        print(f"agent version: {result.agent_version}")
    print(f"report dir: {result.report_dir}")
    print(f"summary: {result.report_dir / 'benchmark_summary.md'}")


def _handle_benchmark_refine(args: argparse.Namespace) -> None:
    result = run_refine_benchmark(
        manifest_path=args.manifest,
        output_dir=args.output_dir,
        venue_profile=args.venue_profile,
        reviewer_specs=_parse_reviewer_specs(args),
        judge_spec=parse_provider_model_spec(getattr(args, "judge", None)),
        use_llm_judge=args.use_llm_judge,
        llm_judge_spec=parse_provider_model_spec(getattr(args, "llm_judge", None)),
        force_bootstrap=args.force_bootstrap,
        timeout_seconds=args.timeout_seconds,
    )
    print("environment check: refine.ink benchmark")
    print(f"cases: {len(result.cases)}")
    print(f"aggregate recall (matched+partial): {result.aggregate_recall:.1%}")
    print(f"aggregate full recall (matched only): {result.aggregate_full_recall:.1%}")
    for c in result.cases:
        matched = sum(1 for m in c.matches if m.status == "matched")
        partial = sum(1 for m in c.matches if m.status == "partial")
        missed = sum(1 for m in c.matches if m.status == "missed")
        print(f"  {c.case_id}: recall={c.recall:.1%} (matched={matched}, partial={partial}, missed={missed}, expected={len(c.expected_comments)}, found={c.our_total_findings})")
    print(f"report dir: {result.report_dir}")
    print(f"summary: {result.report_dir / 'benchmark_summary.md'}")


def _handle_benchmark_ingestion(args: argparse.Namespace) -> None:
    from datetime import datetime

    from .eval.ingestion import (
        build_default_adapters,
        expand_parser_selection,
        load_corpus,
        run_ingestion_benchmark,
    )

    fixtures_root = Path(args.fixtures_root).expanduser().resolve()
    ground_truth_dir = Path(args.ground_truth_dir).expanduser().resolve()

    paper_ids = list(args.paper_id) if args.paper_id else None
    entries = load_corpus(
        fixtures_root,
        limit=None if paper_ids else args.limit,
        paper_ids=paper_ids,
    )
    if not entries:
        print("error: no corpus entries selected")
        raise SystemExit(1)

    all_adapters = build_default_adapters(mineru_timeout_seconds=args.timeout_seconds)
    try:
        selected_adapters = expand_parser_selection(
            args.parsers, all_adapters=all_adapters
        )
    except ValueError as error:
        print(f"error: {error}")
        raise SystemExit(1)
    if not selected_adapters:
        print("error: no parsers selected")
        raise SystemExit(1)

    if args.output_dir:
        output_dir = Path(args.output_dir).expanduser().resolve()
    else:
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        output_dir = Path("benchmarks/ingestion/runs") / timestamp
        output_dir = output_dir.resolve()

    print("environment check: ingestion benchmark")
    print(f"papers: {len(entries)} ({', '.join(e.arxiv_id for e in entries)})")
    print(f"parsers: {', '.join(a.key for a in selected_adapters)}")
    print(f"output dir: {output_dir}")

    run = run_ingestion_benchmark(
        entries=entries,
        adapters=selected_adapters,
        output_dir=output_dir,
        ground_truth_dir=ground_truth_dir,
        skip_ground_truth=args.skip_ground_truth,
        allow_pdf_download=not args.no_pdf_download,
    )

    successes = sum(1 for cell in run.cells if cell.success)
    print(f"cells: {successes}/{len(run.cells)} successful")
    print(f"leaderboard: {output_dir / 'leaderboard.md'}")
    print(f"per-paper: {output_dir / 'per_paper.md'}")


# ── dispatch ─────────────────────────────────────────────────────────

def _handle_ingest(args: argparse.Namespace) -> None:
    import json as _json
    from dataclasses import asdict
    document = parse_document(args.file, parser=args.parser)
    output_data = _json.dumps(asdict(document), indent=2, ensure_ascii=False)
    if args.output:
        Path(args.output).write_text(output_data + "\n", encoding="utf-8")
        print(f"document written to: {args.output}")
    else:
        print(output_data)
    print(f"parser: {document.parser_used}", file=__import__("sys").stderr)
    print(f"title: {document.metadata.title}", file=__import__("sys").stderr)
    print(f"sections: {len(document.sections)}", file=__import__("sys").stderr)


def _handle_serve(args: argparse.Namespace) -> None:
    try:
        import uvicorn
        from .api import app
    except ImportError as error:
        print(
            f"Error: missing dependency for 'revisica serve': {error}\n"
            "Install with: pip install 'revisica[serve]'"
        )
        raise SystemExit(1)
    print(f"Starting Revisica API server on {args.host}:{args.port}")
    uvicorn.run(app, host=args.host, port=args.port)


_HANDLERS = {
    "bootstrap": lambda args: [print(line) for line in bootstrap(targets=args.targets, force=args.force)],
    "serve": _handle_serve,
    "ingest": _handle_ingest,
    "review": _handle_review,
    "writing-review": _handle_writing_review,
    "math-review": _handle_math_review,
    "benchmark-math": _handle_benchmark_math,
    "benchmark-writing": _handle_benchmark_writing,
    "benchmark-history": _handle_benchmark_history,
    "import-proofnet": lambda args: _handle_import_proofnet(args),
    "benchmark-proofnet": lambda args: _handle_benchmark_proofnet(args),
    "benchmark-run": _handle_benchmark_run,
    "benchmark-refine": _handle_benchmark_refine,
    "benchmark-ingestion": _handle_benchmark_ingestion,
}


def _handle_import_proofnet(args: argparse.Namespace) -> None:
    result = import_proofnet_cases(
        split=args.split,
        limit=args.limit,
        output_dir=args.output_dir,
    )
    print("environment check: ProofNet import")
    print(f"split: {result.split}")
    print(f"imported: {result.imported}")
    print(f"output dir: {result.output_dir}")
    print(f"manifest: {result.manifest_path}")


def _handle_benchmark_proofnet(args: argparse.Namespace) -> None:
    result = benchmark_proofnet(
        split=args.split,
        limit=args.limit,
        output_dir=args.output_dir,
        llm_proof_review=args.llm_proof_review,
        targets=args.targets,
        force_bootstrap=args.force_bootstrap,
        timeout_seconds=args.timeout_seconds,
    )
    print("environment check: ProofNet benchmark")
    print(f"split: {result.split}")
    print(f"imported cases: {result.imported_cases}")
    print(f"report dir: {result.report_dir}")
    print(f"summary: {result.report_dir / 'proofnet_benchmark_summary.md'}")


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()
    handler = _HANDLERS.get(args.command)
    if handler:
        handler(args)
    else:
        parser.print_help()
