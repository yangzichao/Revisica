"""Standardized ingestion benchmark.

Runs multiple parsers over a shared arXiv corpus and produces a
leaderboard comparing correctness (vs arxiv API ground truth) and
structural quality.

Primary entry point: :func:`run_ingestion_benchmark`.
"""

from __future__ import annotations

from .adapters import (
    ParserAdapter,
    build_default_adapters,
    expand_parser_selection,
)
from .corpus import (
    CorpusEntry,
    ensure_pdf_for_entry,
    ensure_tex_for_entry,
    load_corpus,
)
from .ground_truth import ArxivMetadata, fetch_arxiv_metadata
from .metrics import CellMetrics, compute_cell_metrics
from .runner import (
    IngestionBenchmarkCell,
    IngestionBenchmarkRun,
    run_ingestion_benchmark,
)

__all__ = [
    "ArxivMetadata",
    "CellMetrics",
    "CorpusEntry",
    "IngestionBenchmarkCell",
    "IngestionBenchmarkRun",
    "ParserAdapter",
    "build_default_adapters",
    "compute_cell_metrics",
    "ensure_pdf_for_entry",
    "ensure_tex_for_entry",
    "expand_parser_selection",
    "fetch_arxiv_metadata",
    "load_corpus",
    "run_ingestion_benchmark",
]
