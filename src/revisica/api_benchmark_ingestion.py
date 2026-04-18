"""Background ingestion-benchmark runner shared by the HTTP API.

Only one run executes at a time; a subsequent start request returns the
already-running state unchanged. The desktop UI polls :func:`snapshot_state`
to render a live progress bar and leaderboard.
"""

from __future__ import annotations

import logging
import threading
import traceback
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from .eval.ingestion import (
    CorpusEntry,
    IngestionBenchmarkCell,
    ParserAdapter,
    build_default_adapters,
    expand_parser_selection,
    load_corpus,
    run_ingestion_benchmark,
)

logger = logging.getLogger(__name__)


# ── state shape ────────────────────────────────────────────────────────


@dataclass
class BenchmarkRunState:
    """A point-in-time snapshot of a benchmark run.

    Kept intentionally JSON-friendly: every field serializes via
    :func:`dataclasses.asdict` with no custom encoders.
    """

    run_id: str
    status: str                           # "running" | "succeeded" | "failed"
    config: dict[str, Any]
    started_at: str
    finished_at: str | None = None
    output_dir: str = ""
    adapter_keys: list[str] = field(default_factory=list)
    paper_ids: list[str] = field(default_factory=list)
    total_cells: int = 0
    completed_cells: int = 0
    current_paper_id: str | None = None
    current_parser_key: str | None = None
    current_cell_started_at: str | None = None
    cells: list[dict[str, Any]] = field(default_factory=list)
    leaderboard_markdown: str = ""
    per_paper_markdown: str = ""
    error: str | None = None


# ── module-level state ─────────────────────────────────────────────────


_state_lock = threading.Lock()
_current_state: BenchmarkRunState | None = None


# ── public API ─────────────────────────────────────────────────────────


def start_benchmark(config: dict[str, Any]) -> BenchmarkRunState:
    """Start a new benchmark run in a background thread.

    Corpus loading and parser selection happen synchronously in the
    caller's thread so malformed requests fail fast with ``ValueError``
    (surfaced as HTTP 400) rather than starting a "running" state that
    silently transitions to "failed" moments later. The initial state
    also includes the resolved ``paper_ids`` / ``adapter_keys`` /
    ``total_cells`` so the UI progress bar has a real denominator on
    the very first poll.

    If another run is still in progress, returns that run's state
    unchanged (idempotent, so a double-click in the UI does not queue a
    second run).
    """
    global _current_state

    config_snapshot = _validated_config(config)
    entries, adapters = _resolve_corpus_and_adapters(config_snapshot)

    with _state_lock:
        if _current_state is not None and _current_state.status == "running":
            return _clone_state(_current_state)

        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        output_dir = _resolve_output_dir(config_snapshot, timestamp)
        state = BenchmarkRunState(
            run_id=timestamp,
            status="running",
            config=config_snapshot,
            started_at=datetime.now().isoformat(timespec="seconds"),
            output_dir=str(output_dir),
            paper_ids=[entry.arxiv_id for entry in entries],
            adapter_keys=[adapter.key for adapter in adapters],
            total_cells=len(entries) * len(adapters),
        )
        _current_state = state
        snapshot_for_caller = _clone_state(state)

    thread = threading.Thread(
        target=_run_and_capture,
        args=(state, config_snapshot, output_dir, entries, adapters),
        name=f"benchmark-ingestion-{state.run_id}",
        daemon=True,
    )
    thread.start()
    return snapshot_for_caller


def _resolve_corpus_and_adapters(
    config: dict[str, Any],
) -> tuple[list[CorpusEntry], list[ParserAdapter]]:
    """Load the corpus and resolve parser selection eagerly.

    Raises ``ValueError`` on bad configuration so the HTTP layer can
    return 400 before any background work starts.
    """
    fixtures_root = Path(config["fixtures_root"]).expanduser().resolve()
    paper_ids_filter = config.get("paper_ids") or None
    entries = load_corpus(
        fixtures_root,
        limit=None if paper_ids_filter else config.get("limit"),
        paper_ids=paper_ids_filter,
    )
    if not entries:
        raise ValueError("no corpus entries matched the supplied configuration")

    all_adapters = build_default_adapters(
        mineru_timeout_seconds=config.get("timeout_seconds", 900)
    )
    adapters = expand_parser_selection(
        config.get("parsers") or ["all"], all_adapters=all_adapters
    )
    if not adapters:
        raise ValueError("no parsers selected")
    return entries, adapters


def snapshot_state() -> BenchmarkRunState | None:
    """Return a deep copy of the current run state, or ``None`` if never run."""
    with _state_lock:
        if _current_state is None:
            return None
        return _clone_state(_current_state)


# ── run thread ─────────────────────────────────────────────────────────


def _run_and_capture(
    state: BenchmarkRunState,
    config: dict[str, Any],
    output_dir: Path,
    entries: list[CorpusEntry],
    adapters: list[ParserAdapter],
) -> None:
    try:
        ground_truth_dir = Path(config["ground_truth_dir"]).expanduser().resolve()

        def on_run_start(total: int, papers: list[str], keys: list[str]) -> None:
            with _state_lock:
                state.total_cells = total
                state.paper_ids = list(papers)
                state.adapter_keys = list(keys)

        def on_cell_start(paper_id: str, parser_key: str,
                          completed: int, total: int) -> None:
            with _state_lock:
                state.current_paper_id = paper_id
                state.current_parser_key = parser_key
                state.current_cell_started_at = datetime.now().isoformat(
                    timespec="seconds"
                )
                state.completed_cells = completed
                state.total_cells = total

        def on_cell_finish(cell: IngestionBenchmarkCell,
                           completed: int, total: int) -> None:
            with _state_lock:
                state.completed_cells = completed
                state.total_cells = total
                state.cells.append(asdict(cell))
                state.current_paper_id = None
                state.current_parser_key = None
                state.current_cell_started_at = None

        def on_run_finish(_run) -> None:
            leaderboard = output_dir / "leaderboard.md"
            per_paper = output_dir / "per_paper.md"
            with _state_lock:
                if leaderboard.exists():
                    state.leaderboard_markdown = leaderboard.read_text(encoding="utf-8")
                if per_paper.exists():
                    state.per_paper_markdown = per_paper.read_text(encoding="utf-8")

        run_ingestion_benchmark(
            entries=entries,
            adapters=adapters,
            output_dir=output_dir,
            ground_truth_dir=ground_truth_dir,
            skip_ground_truth=bool(config.get("skip_ground_truth", False)),
            allow_pdf_download=not bool(config.get("no_pdf_download", False)),
            on_run_start=on_run_start,
            on_cell_start=on_cell_start,
            on_cell_finish=on_cell_finish,
            on_run_finish=on_run_finish,
        )
        with _state_lock:
            state.status = "succeeded"
            state.finished_at = datetime.now().isoformat(timespec="seconds")
    except Exception as error:  # noqa: BLE001 — surface every failure to the UI
        logger.exception("benchmark run failed")
        with _state_lock:
            state.status = "failed"
            state.finished_at = datetime.now().isoformat(timespec="seconds")
            state.error = _summarize_exception(error)


# ── helpers ────────────────────────────────────────────────────────────


def _validated_config(raw: dict[str, Any]) -> dict[str, Any]:
    """Freeze user-supplied config into a normalized snapshot."""
    parsers = raw.get("parsers") or ["all"]
    if not isinstance(parsers, list) or not all(isinstance(p, str) for p in parsers):
        raise ValueError("parsers must be a list of strings")
    limit = int(raw.get("limit", 3))
    if limit < 1 or limit > 24:
        raise ValueError("limit must be between 1 and 24")
    paper_ids = raw.get("paper_ids")
    if paper_ids is not None:
        if not isinstance(paper_ids, list) or not all(
            isinstance(i, str) for i in paper_ids
        ):
            raise ValueError("paper_ids must be a list of strings if supplied")
    timeout_seconds = int(raw.get("timeout_seconds", 900))
    if timeout_seconds < 30 or timeout_seconds > 3600:
        raise ValueError("timeout_seconds must be between 30 and 3600")
    return {
        "parsers": parsers,
        "limit": limit,
        "paper_ids": paper_ids,
        "skip_ground_truth": bool(raw.get("skip_ground_truth", False)),
        "no_pdf_download": bool(raw.get("no_pdf_download", False)),
        "timeout_seconds": timeout_seconds,
        "fixtures_root": raw.get("fixtures_root") or "tests/fixtures/arxiv",
        "ground_truth_dir":
            raw.get("ground_truth_dir") or "benchmarks/ingestion/ground_truth",
    }


def _resolve_output_dir(config: dict[str, Any], timestamp: str) -> Path:
    override = config.get("output_dir")
    if override:
        return Path(override).expanduser().resolve()
    return (Path("benchmarks/ingestion/runs") / timestamp).resolve()


def _clone_state(state: BenchmarkRunState) -> BenchmarkRunState:
    """Return a copy safe to release outside the lock.

    Mutable child collections (cells list, config dict) are shallow-copied
    so the caller can't mutate live state.
    """
    return BenchmarkRunState(
        run_id=state.run_id,
        status=state.status,
        config=dict(state.config),
        started_at=state.started_at,
        finished_at=state.finished_at,
        output_dir=state.output_dir,
        adapter_keys=list(state.adapter_keys),
        paper_ids=list(state.paper_ids),
        total_cells=state.total_cells,
        completed_cells=state.completed_cells,
        current_paper_id=state.current_paper_id,
        current_parser_key=state.current_parser_key,
        current_cell_started_at=state.current_cell_started_at,
        cells=list(state.cells),
        leaderboard_markdown=state.leaderboard_markdown,
        per_paper_markdown=state.per_paper_markdown,
        error=state.error,
    )


def _summarize_exception(error: Exception) -> str:
    message = str(error) or traceback.format_exception_only(
        type(error), error
    )[0].strip()
    return message[:1000]


# ── adapter availability probe (for the UI config form) ────────────────


def list_available_parsers() -> list[dict[str, Any]]:
    """Enumerate every adapter with its availability for the UI to render."""
    adapters = build_default_adapters()
    rows: list[dict[str, Any]] = []
    for adapter in adapters:
        ok, reason = adapter.availability()
        rows.append({
            "key": adapter.key,
            "family": adapter.family,
            "requires_format": adapter.requires_format,
            "available": ok,
            "skip_reason": reason,
        })
    return rows
