"""Ingestion benchmark orchestrator.

Iterates (paper × parser) cells, invokes each adapter with a timeout,
records metrics, and writes a leaderboard + per-paper drill-down to a
timestamped run directory.
"""

from __future__ import annotations

import json
import logging
import subprocess
import time
import traceback
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Callable

from .adapters import ParserAdapter
from .corpus import (
    CorpusEntry,
    ensure_pdf_for_entry,
    ensure_tex_for_entry,
)
from .ground_truth import ArxivMetadata, fetch_arxiv_metadata
from .metrics import CellMetrics, compute_cell_metrics

logger = logging.getLogger(__name__)


# ── data shapes ────────────────────────────────────────────────────────


@dataclass
class IngestionBenchmarkCell:
    """One (paper, parser) outcome."""

    paper_id: str
    parser_key: str
    requires_format: str
    success: bool
    duration_seconds: float
    error_kind: str | None = None
    error_message: str | None = None
    metrics: CellMetrics | None = None
    artifact_path: str | None = None


@dataclass
class IngestionBenchmarkRun:
    """Complete benchmark output, persisted under *output_dir*."""

    output_dir: Path
    started_at: str
    finished_at: str
    papers_attempted: list[str]
    parsers_attempted: list[str]
    cells: list[IngestionBenchmarkCell] = field(default_factory=list)


# ── public entry point ────────────────────────────────────────────────


CellStartCallback = Callable[[str, str, int, int], None]
CellFinishCallback = Callable[["IngestionBenchmarkCell", int, int], None]
RunStartCallback = Callable[[int, list[str], list[str]], None]
RunFinishCallback = Callable[["IngestionBenchmarkRun"], None]


def run_ingestion_benchmark(
    entries: list[CorpusEntry],
    adapters: list[ParserAdapter],
    *,
    output_dir: Path,
    ground_truth_dir: Path,
    skip_ground_truth: bool = False,
    allow_pdf_download: bool = True,
    on_run_start: RunStartCallback | None = None,
    on_cell_start: CellStartCallback | None = None,
    on_cell_finish: CellFinishCallback | None = None,
    on_run_finish: RunFinishCallback | None = None,
) -> IngestionBenchmarkRun:
    """Run every ``(entry, adapter)`` cell and write the report.

    Failed adapters and missing inputs produce structured cells with
    ``success=False`` rather than aborting the run. Every cell's raw
    markdown is written to ``output_dir/artifacts/<paper>/<adapter>.md``
    for manual inspection.

    Optional callbacks let a caller (e.g. the HTTP API) observe progress:

    - ``on_run_start(total_cells, paper_ids, parser_keys)`` fires once
      before any cell runs, so listeners can size a progress bar.
    - ``on_cell_start(paper_id, parser_key, completed, total)`` fires
      immediately before each parse attempt.
    - ``on_cell_finish(cell, completed, total)`` fires after each cell
      settles (success, timeout, or failure). ``completed`` is the
      number of cells finished so far including this one.
    - ``on_run_finish(run)`` fires once after everything is written to
      disk.

    Callbacks must not raise — they are invoked inside the run loop and
    exceptions propagate and abort the benchmark.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    artifacts_dir = output_dir / "artifacts"
    artifacts_dir.mkdir(exist_ok=True)
    results_jsonl = output_dir / "results.jsonl"
    results_jsonl.write_text("", encoding="utf-8")

    started_at = datetime.now().isoformat(timespec="seconds")
    run = IngestionBenchmarkRun(
        output_dir=output_dir,
        started_at=started_at,
        finished_at="",
        papers_attempted=[entry.arxiv_id for entry in entries],
        parsers_attempted=[adapter.key for adapter in adapters],
    )

    adapter_availability: dict[str, tuple[bool, str | None]] = {
        adapter.key: adapter.availability() for adapter in adapters
    }
    needs_pdf = any(adapter.requires_format == "pdf" for adapter in adapters)
    needs_tex = any(adapter.requires_format == "tex" for adapter in adapters)

    ground_truth_by_id: dict[str, ArxivMetadata | None] = {}
    if not skip_ground_truth:
        for entry in entries:
            ground_truth_by_id[entry.arxiv_id] = fetch_arxiv_metadata(
                entry.arxiv_id, ground_truth_dir
            )
    else:
        for entry in entries:
            ground_truth_by_id[entry.arxiv_id] = None

    total_cells = len(entries) * len(adapters)
    completed_cells = 0

    if on_run_start is not None:
        on_run_start(
            total_cells,
            [entry.arxiv_id for entry in entries],
            [adapter.key for adapter in adapters],
        )

    for entry in entries:
        paper_artifacts_dir = artifacts_dir / entry.arxiv_id
        paper_artifacts_dir.mkdir(exist_ok=True)

        tex_path = ensure_tex_for_entry(entry) if needs_tex else None
        pdf_path = (
            ensure_pdf_for_entry(entry) if (needs_pdf and allow_pdf_download) else None
        )

        for adapter in adapters:
            if on_cell_start is not None:
                on_cell_start(
                    entry.arxiv_id, adapter.key, completed_cells, total_cells
                )
            cell = _run_one_cell(
                entry=entry,
                adapter=adapter,
                availability=adapter_availability[adapter.key],
                tex_path=tex_path,
                pdf_path=pdf_path,
                ground_truth=ground_truth_by_id[entry.arxiv_id],
                artifacts_dir=paper_artifacts_dir,
            )
            run.cells.append(cell)
            _append_jsonl(results_jsonl, cell)
            completed_cells += 1
            if on_cell_finish is not None:
                on_cell_finish(cell, completed_cells, total_cells)

    run.finished_at = datetime.now().isoformat(timespec="seconds")

    _write_config(output_dir, entries, adapters, skip_ground_truth)
    _write_leaderboard(output_dir, run)
    _write_per_paper(output_dir, run, ground_truth_by_id)

    if on_run_finish is not None:
        on_run_finish(run)

    return run


# ── cell execution ─────────────────────────────────────────────────────


def _run_one_cell(
    *,
    entry: CorpusEntry,
    adapter: ParserAdapter,
    availability: tuple[bool, str | None],
    tex_path: Path | None,
    pdf_path: Path | None,
    ground_truth: ArxivMetadata | None,
    artifacts_dir: Path,
) -> IngestionBenchmarkCell:
    ok, skip_reason = availability
    if not ok:
        return IngestionBenchmarkCell(
            paper_id=entry.arxiv_id,
            parser_key=adapter.key,
            requires_format=adapter.requires_format,
            success=False,
            duration_seconds=0.0,
            error_kind="unavailable",
            error_message=skip_reason or "adapter unavailable",
        )

    input_path = tex_path if adapter.requires_format == "tex" else pdf_path
    if input_path is None:
        return IngestionBenchmarkCell(
            paper_id=entry.arxiv_id,
            parser_key=adapter.key,
            requires_format=adapter.requires_format,
            success=False,
            duration_seconds=0.0,
            error_kind="input_missing",
            error_message=f"no {adapter.requires_format} input for {entry.arxiv_id}",
        )

    logger.info("parsing %s with %s", entry.arxiv_id, adapter.key)
    started = time.monotonic()
    try:
        markdown = adapter.parse(input_path)
    except subprocess.TimeoutExpired as error:
        duration = time.monotonic() - started
        return IngestionBenchmarkCell(
            paper_id=entry.arxiv_id,
            parser_key=adapter.key,
            requires_format=adapter.requires_format,
            success=False,
            duration_seconds=duration,
            error_kind="timeout",
            error_message=f"timed out after {duration:.1f}s: {error}"[:500],
        )
    except Exception as error:  # noqa: BLE001 — we genuinely want to report any failure
        duration = time.monotonic() - started
        logger.warning(
            "parse failed for %s / %s: %s",
            entry.arxiv_id, adapter.key, error,
        )
        return IngestionBenchmarkCell(
            paper_id=entry.arxiv_id,
            parser_key=adapter.key,
            requires_format=adapter.requires_format,
            success=False,
            duration_seconds=duration,
            error_kind="parse_failed",
            error_message=_summarize_exception(error),
        )

    duration = time.monotonic() - started

    artifact_path = artifacts_dir / f"{adapter.key.replace(':', '-')}.md"
    artifact_path.write_text(markdown, encoding="utf-8")

    cell_metrics = compute_cell_metrics(markdown, ground_truth)

    return IngestionBenchmarkCell(
        paper_id=entry.arxiv_id,
        parser_key=adapter.key,
        requires_format=adapter.requires_format,
        success=True,
        duration_seconds=duration,
        metrics=cell_metrics,
        artifact_path=str(artifact_path),
    )


def _summarize_exception(error: Exception) -> str:
    message = str(error)
    if message:
        return message[:500]
    return traceback.format_exception_only(type(error), error)[0].strip()[:500]


# ── result persistence ─────────────────────────────────────────────────


def _append_jsonl(path: Path, cell: IngestionBenchmarkCell) -> None:
    payload = asdict(cell)
    # dataclass.asdict recurses into CellMetrics; Path objects are already strings.
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


def _write_config(
    output_dir: Path,
    entries: list[CorpusEntry],
    adapters: list[ParserAdapter],
    skip_ground_truth: bool,
) -> None:
    payload = {
        "entries": [
            {"arxiv_id": entry.arxiv_id, "field": entry.field}
            for entry in entries
        ],
        "adapters": [adapter.key for adapter in adapters],
        "skip_ground_truth": skip_ground_truth,
    }
    (output_dir / "config.json").write_text(
        json.dumps(payload, indent=2), encoding="utf-8"
    )


# ── leaderboard.md ─────────────────────────────────────────────────────


def _write_leaderboard(output_dir: Path, run: IngestionBenchmarkRun) -> None:
    """Aggregate stats per parser across all papers."""
    lines: list[str] = []
    lines.append("# Ingestion Benchmark — Leaderboard")
    lines.append("")
    lines.append(f"- Started: {run.started_at}")
    lines.append(f"- Finished: {run.finished_at}")
    lines.append(f"- Papers: {len(run.papers_attempted)} "
                 f"({', '.join(run.papers_attempted)})")
    lines.append("")

    per_parser_cells: dict[str, list[IngestionBenchmarkCell]] = {}
    for cell in run.cells:
        per_parser_cells.setdefault(cell.parser_key, []).append(cell)

    header = (
        "| Parser | N | Success | Avg time | Title match | Authors F1 | "
        "Abstract overlap | Has math | Clean titles | Leftover LaTeX | "
        "Avg md length |"
    )
    separator = (
        "|--------|---|---------|----------|-------------|------------|"
        "------------------|----------|--------------|----------------|"
        "---------------|"
    )
    lines.append(header)
    lines.append(separator)

    for parser_key in run.parsers_attempted:
        cells = per_parser_cells.get(parser_key, [])
        lines.append(_format_leaderboard_row(parser_key, cells))

    lines.append("")
    lines.append("## Column meaning")
    lines.append("")
    lines.append("- **Title match** — fraction of papers where the extracted "
                 "title fuzzy-matches the arXiv ground truth (threshold 0.9).")
    lines.append("- **Authors F1** — average F1 of extracted-vs-ground-truth "
                 "surname sets.")
    lines.append("- **Abstract overlap** — average Jaccard of extracted "
                 "abstract tokens vs ground truth.")
    lines.append("- **Has math** — fraction of papers with any inline or "
                 "display math in the output.")
    lines.append("- **Clean titles** — fraction of papers whose extracted "
                 "headings are free of raw LaTeX (`\\`, `{`).")
    lines.append("- **Leftover LaTeX** — average count of distinct raw "
                 "LaTeX command prefixes still present in the markdown.")

    (output_dir / "leaderboard.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )


def _format_leaderboard_row(
    parser_key: str, cells: list[IngestionBenchmarkCell]
) -> str:
    if not cells:
        return (
            f"| `{parser_key}` | 0 | — | — | — | — | — | — | — | — | — |"
        )

    successes = [cell for cell in cells if cell.success]
    success_rate = f"{len(successes)}/{len(cells)}"
    avg_duration = _average(cell.duration_seconds for cell in cells if cell.success)

    def ratio_of(predicate) -> str:
        matched_cells = [cell for cell in successes if predicate(cell)]
        return _percent_or_dash(matched_cells, successes)

    def ratio_of_optional(extractor) -> str:
        """Fraction over cells whose metric is not ``None`` (i.e. scored)."""
        scored = [cell for cell in successes if extractor(cell) is not None]
        if not scored:
            return "—"
        matched = [cell for cell in scored if extractor(cell)]
        return f"{len(matched) / len(scored) * 100:.0f}%"

    def avg_metric(extractor) -> str:
        values = [extractor(cell) for cell in successes if extractor(cell) is not None]
        if not values:
            return "—"
        return f"{sum(values) / len(values):.2f}"

    def avg_int_metric(extractor) -> str:
        values = [extractor(cell) for cell in successes]
        if not values:
            return "—"
        return f"{sum(values) / len(values):.1f}"

    title_match = ratio_of_optional(
        lambda cell: cell.metrics.title_match_ok if cell.metrics else None
    )
    authors_f1 = avg_metric(
        lambda cell: cell.metrics.authors_f1 if cell.metrics else None
    )
    abstract_overlap = avg_metric(
        lambda cell: cell.metrics.abstract_overlap_ratio if cell.metrics else None
    )
    has_math = ratio_of(
        lambda cell: cell.metrics is not None and cell.metrics.has_math
    )
    clean_titles = ratio_of(
        lambda cell: cell.metrics is not None and cell.metrics.clean_heading_titles
    )
    leftover = avg_int_metric(
        lambda cell: len(cell.metrics.leftover_latex_commands) if cell.metrics else 0
    )
    avg_md_length = avg_int_metric(
        lambda cell: cell.metrics.markdown_length if cell.metrics else 0
    )

    return (
        f"| `{parser_key}` | {len(cells)} | {success_rate} | "
        f"{_format_seconds(avg_duration)} | {title_match} | {authors_f1} | "
        f"{abstract_overlap} | {has_math} | {clean_titles} | {leftover} | "
        f"{avg_md_length} |"
    )


def _average(values) -> float:
    values_list = list(values)
    if not values_list:
        return 0.0
    return sum(values_list) / len(values_list)


def _format_seconds(duration: float) -> str:
    if duration <= 0:
        return "—"
    if duration < 60:
        return f"{duration:.1f}s"
    return f"{duration / 60:.1f}m"


def _percent_or_dash(numerator, denominator) -> str:
    if not denominator:
        return "—"
    return f"{len(numerator) / len(denominator) * 100:.0f}%"


# ── per_paper.md ───────────────────────────────────────────────────────


def _write_per_paper(
    output_dir: Path,
    run: IngestionBenchmarkRun,
    ground_truth_by_id: dict[str, ArxivMetadata | None],
) -> None:
    lines: list[str] = []
    lines.append("# Ingestion Benchmark — Per Paper")
    lines.append("")

    cells_by_paper: dict[str, list[IngestionBenchmarkCell]] = {}
    for cell in run.cells:
        cells_by_paper.setdefault(cell.paper_id, []).append(cell)

    for paper_id in run.papers_attempted:
        lines.append(f"## {paper_id}")
        lines.append("")
        ground_truth = ground_truth_by_id.get(paper_id)
        if ground_truth is not None:
            lines.append(f"**Ground-truth title:** {ground_truth.title}")
            lines.append("")
            lines.append(
                f"**Ground-truth authors:** {', '.join(ground_truth.authors) or '—'}"
            )
            lines.append("")
        else:
            lines.append("_No ground truth available for this paper._")
            lines.append("")

        lines.append(
            "| Parser | Status | Time | Extracted title | Title match | "
            "Authors F1 | Abstract overlap | Math (inline/display) | "
            "Headings | Leftover LaTeX | Artifact |"
        )
        lines.append(
            "|--------|--------|------|-----------------|-------------|"
            "------------|------------------|------------------------|"
            "----------|----------------|----------|"
        )

        for cell in cells_by_paper.get(paper_id, []):
            lines.append(_format_per_paper_row(cell))

        lines.append("")

    (output_dir / "per_paper.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )


def _format_per_paper_row(cell: IngestionBenchmarkCell) -> str:
    status = "✅" if cell.success else f"❌ {cell.error_kind or 'failed'}"
    time_display = _format_seconds(cell.duration_seconds) if cell.success else "—"
    if cell.metrics is None:
        return (
            f"| `{cell.parser_key}` | {status} | {time_display} | "
            f"— | — | — | — | — | — | — | — |"
        )
    metrics = cell.metrics
    title_preview = (metrics.extracted_title or "—").replace("|", "\\|")
    if len(title_preview) > 60:
        title_preview = title_preview[:60] + "…"
    title_match = (
        f"{metrics.title_match_ratio:.2f}"
        if metrics.title_match_ratio is not None else "—"
    )
    authors_f1 = (
        f"{metrics.authors_f1:.2f}"
        if metrics.authors_f1 is not None else "—"
    )
    abstract_overlap = (
        f"{metrics.abstract_overlap_ratio:.2f}"
        if metrics.abstract_overlap_ratio is not None else "—"
    )
    math_display = f"{metrics.inline_math_count}/{metrics.display_math_count}"
    leftover_display = (
        ", ".join(metrics.leftover_latex_commands) or "0"
    )
    # per_paper.md lives at <output_dir>/per_paper.md while artifacts are
    # written to <output_dir>/artifacts/<paper>/<parser>.md — the link has
    # to be relative to per_paper.md for the markdown to resolve.
    artifact_display = (
        f"[md](artifacts/{cell.paper_id}/{Path(cell.artifact_path).name})"
        if cell.artifact_path else "—"
    )
    return (
        f"| `{cell.parser_key}` | {status} | {time_display} | "
        f"{title_preview} | {title_match} | {authors_f1} | {abstract_overlap} | "
        f"{math_display} | {metrics.heading_count} | {leftover_display} | "
        f"{artifact_display} |"
    )
