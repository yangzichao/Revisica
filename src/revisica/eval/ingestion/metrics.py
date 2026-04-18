"""Per-cell metric computation for the ingestion benchmark.

A **cell** is one (paper, parser) outcome: either a raw-markdown string
to score, or a parse failure. :func:`compute_cell_metrics` turns the
first into a structured :class:`CellMetrics`; the runner handles the
failure case itself.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from difflib import SequenceMatcher

from revisica.ingestion.markdown_metrics import (
    collect_heading_titles,
    count_display_math,
    count_headings,
    count_inline_math,
    detect_leftover_latex_commands,
    dirty_section_titles,
    extract_abstract,
    extract_authors,
    extract_title,
    normalize_for_comparison,
    tokenize,
)

from .ground_truth import ArxivMetadata


# ── thresholds ─────────────────────────────────────────────────────────


TITLE_MATCH_THRESHOLD: float = 0.9
ABSTRACT_OVERLAP_THRESHOLD: float = 0.6


# ── data shape ─────────────────────────────────────────────────────────


@dataclass
class CellMetrics:
    """Every scalar and derived flag for one parser × paper cell."""

    # Raw extracted content
    markdown_length: int
    extracted_title: str
    extracted_authors: list[str] = field(default_factory=list)
    extracted_abstract_prefix: str = ""

    # Structural counts
    heading_count: int = 0
    inline_math_count: int = 0
    display_math_count: int = 0
    leftover_latex_commands: list[str] = field(default_factory=list)
    dirty_heading_titles: list[str] = field(default_factory=list)

    # Ground-truth correctness (only meaningful if ground_truth is provided)
    title_match_ratio: float | None = None
    title_match_ok: bool | None = None
    authors_f1: float | None = None
    authors_match_ok: bool | None = None
    abstract_overlap_ratio: float | None = None
    abstract_overlap_ok: bool | None = None

    # Derived structural flags (ground-truth-free)
    has_math: bool = False
    clean_heading_titles: bool = False
    no_leftover_commands: bool = False


# ── entry point ────────────────────────────────────────────────────────


def compute_cell_metrics(
    markdown: str,
    ground_truth: ArxivMetadata | None,
) -> CellMetrics:
    """Score one parser's raw Markdown output against optional ground truth."""
    extracted_title = extract_title(markdown)
    extracted_authors = extract_authors(markdown)
    extracted_abstract = extract_abstract(markdown)

    inline_count = count_inline_math(markdown)
    display_count = count_display_math(markdown)
    leftover_commands = detect_leftover_latex_commands(markdown)
    dirty_titles = dirty_section_titles(markdown)

    cell = CellMetrics(
        markdown_length=len(markdown),
        extracted_title=extracted_title,
        extracted_authors=extracted_authors,
        extracted_abstract_prefix=extracted_abstract[:400],
        heading_count=count_headings(markdown),
        inline_math_count=inline_count,
        display_math_count=display_count,
        leftover_latex_commands=leftover_commands,
        dirty_heading_titles=dirty_titles,
        has_math=(inline_count + display_count) > 0,
        clean_heading_titles=len(dirty_titles) == 0
            and len(collect_heading_titles(markdown)) > 0,
        no_leftover_commands=len(leftover_commands) == 0,
    )

    if ground_truth is not None:
        _score_against_ground_truth(cell, extracted_abstract, ground_truth)

    return cell


# ── ground-truth scoring ───────────────────────────────────────────────


def _score_against_ground_truth(
    cell: CellMetrics,
    extracted_abstract: str,
    ground_truth: ArxivMetadata,
) -> None:
    cell.title_match_ratio = fuzzy_title_match_ratio(
        cell.extracted_title, ground_truth.title
    )
    cell.title_match_ok = cell.title_match_ratio >= TITLE_MATCH_THRESHOLD

    cell.authors_f1 = authors_f1_score(cell.extracted_authors, ground_truth.authors)
    cell.authors_match_ok = cell.authors_f1 >= 0.5

    cell.abstract_overlap_ratio = abstract_overlap_ratio(
        extracted_abstract, ground_truth.abstract
    )
    cell.abstract_overlap_ok = cell.abstract_overlap_ratio >= ABSTRACT_OVERLAP_THRESHOLD


# ── fuzzy matching helpers ─────────────────────────────────────────────


def fuzzy_title_match_ratio(extracted: str, reference: str) -> float:
    """Ratio ∈ [0, 1] of how closely *extracted* matches *reference*.

    Uses :class:`difflib.SequenceMatcher` over normalized token sequences,
    which tolerates word reordering and punctuation differences better
    than character-level matching.
    """
    if not extracted or not reference:
        return 0.0
    lhs = normalize_for_comparison(extracted)
    rhs = normalize_for_comparison(reference)
    if not lhs or not rhs:
        return 0.0
    return SequenceMatcher(None, lhs, rhs).ratio()


def authors_f1_score(extracted: list[str], reference: list[str]) -> float:
    """F1 between extracted and reference author **surname** sets.

    Matching on surnames only is more robust to "F. Last" vs "First Last"
    formatting differences — the benchmark is testing whether the *set*
    of people is recovered, not name formatting.
    """
    if not extracted and not reference:
        return 1.0
    if not extracted or not reference:
        return 0.0

    extracted_surnames = {_surname(name) for name in extracted if name.strip()}
    reference_surnames = {_surname(name) for name in reference if name.strip()}
    extracted_surnames.discard("")
    reference_surnames.discard("")

    if not extracted_surnames or not reference_surnames:
        return 0.0

    true_positives = len(extracted_surnames & reference_surnames)
    if true_positives == 0:
        return 0.0
    precision = true_positives / len(extracted_surnames)
    recall = true_positives / len(reference_surnames)
    return 2 * precision * recall / (precision + recall)


def _surname(name: str) -> str:
    tokens = normalize_for_comparison(name).split()
    return tokens[-1] if tokens else ""


def abstract_overlap_ratio(extracted: str, reference: str) -> float:
    """Jaccard overlap on normalized token sets between abstracts.

    Uses set overlap rather than character similarity because parsers
    reorder/rewrap abstract text differently; what matters is whether
    the same *content words* appear.
    """
    if not extracted or not reference:
        return 0.0
    extracted_tokens = tokenize(extracted)
    reference_tokens = tokenize(reference)
    if not extracted_tokens or not reference_tokens:
        return 0.0
    intersection = extracted_tokens & reference_tokens
    union = extracted_tokens | reference_tokens
    return len(intersection) / len(union)
