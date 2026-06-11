"""Resolve finding anchors against the reviewed document text.

Anchoring is quote-first: reviewer-supplied snippets are matched against
the document with whitespace-insensitive search (LLM line numbers are
unreliable; verbatim quotes are not). Tiers, strongest first:

1. ``exact``      — the quote (or its longest usable line) matched; the
                    anchor gets char offsets, a line number, and a section.
2. ``line``       — no quote match, but the lane reported a line number
                    that exists in the document (deterministic math checks
                    always do); the anchor covers that whole line.
3. ``unresolved`` — nothing usable; the finding is shown without an
                    in-document highlight.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .types import (
    RESOLUTION_EXACT,
    RESOLUTION_LINE,
    RESOLUTION_UNRESOLVED,
    UnifiedFinding,
    severity_rank,
)

if TYPE_CHECKING:
    from ..ingestion.types import DocumentSection

# A quote line shorter than this (after whitespace collapsing) is too
# ambiguous to use as a fallback search needle.
MIN_FALLBACK_NEEDLE_LENGTH = 20


def resolve_anchors(
    findings: list[UnifiedFinding],
    document_text: str,
    sections: "list[DocumentSection] | None" = None,
) -> None:
    """Resolve every anchor in place, then sort findings in document order.

    Sorting puts resolved findings in reading order with unresolved ones
    last, and re-assigns sequential ids so ``f-001`` is the first
    annotation in the document.
    """
    normalized_doc, offset_map = _normalize_with_offset_map(document_text)
    line_starts = _line_start_offsets(document_text)
    flat_sections = _flatten_sections(sections or [])

    for finding in findings:
        _resolve_one(finding, document_text, normalized_doc, offset_map, line_starts)
        _attach_section(finding, flat_sections)

    findings.sort(key=_document_order_key)
    for index, finding in enumerate(findings, start=1):
        finding.id = f"f-{index:03d}"


def _resolve_one(
    finding: UnifiedFinding,
    document_text: str,
    normalized_doc: str,
    offset_map: list[int],
    line_starts: list[int],
) -> None:
    anchor = finding.anchor
    span = _match_quote(
        anchor.quote, normalized_doc, offset_map, anchor.line_number, document_text
    )
    if span is not None:
        anchor.start_offset, anchor.end_offset = span
        anchor.line_number = _offset_to_line(document_text, anchor.start_offset)
        anchor.resolution = RESOLUTION_EXACT
        return
    if anchor.line_number is not None and 1 <= anchor.line_number <= len(line_starts):
        start = line_starts[anchor.line_number - 1]
        end = document_text.find("\n", start)
        anchor.start_offset = start
        anchor.end_offset = len(document_text) if end == -1 else end
        anchor.resolution = RESOLUTION_LINE
        return
    anchor.line_number = None
    anchor.resolution = RESOLUTION_UNRESOLVED


def _match_quote(
    quote: str,
    normalized_doc: str,
    offset_map: list[int],
    hint_line: int | None,
    document_text: str,
) -> tuple[int, int] | None:
    """Find the quote in the document; returns original-text char offsets."""
    needles = [_collapse_whitespace(quote)]
    fallback = _longest_quote_line(quote)
    if fallback and fallback not in needles:
        needles.append(fallback)
    for needle in needles:
        if len(needle) < 3:
            continue
        positions = _find_all(normalized_doc, needle)
        if not positions:
            continue
        start_norm = _pick_nearest(positions, hint_line, offset_map, document_text)
        end_norm = start_norm + len(needle) - 1
        return offset_map[start_norm], offset_map[end_norm] + 1
    return None


def _pick_nearest(
    positions: list[int],
    hint_line: int | None,
    offset_map: list[int],
    document_text: str,
) -> int:
    if hint_line is None or len(positions) == 1:
        return positions[0]
    return min(
        positions,
        key=lambda pos: abs(_offset_to_line(document_text, offset_map[pos]) - hint_line),
    )


# ── text utilities ──────────────────────────────────────────────────


def _collapse_whitespace(text: str) -> str:
    return " ".join(text.split())


def _longest_quote_line(quote: str) -> str | None:
    lines = [_collapse_whitespace(line) for line in quote.splitlines()]
    lines = [line for line in lines if len(line) >= MIN_FALLBACK_NEEDLE_LENGTH]
    return max(lines, key=len) if lines else None


def _normalize_with_offset_map(text: str) -> tuple[str, list[int]]:
    """Collapse whitespace runs to single spaces, keeping an index map.

    ``offset_map[i]`` is the offset in the original text of the character
    at position ``i`` in the normalized text.
    """
    chars: list[str] = []
    offset_map: list[int] = []
    in_whitespace = False
    for index, char in enumerate(text):
        if char.isspace():
            if in_whitespace:
                continue
            chars.append(" ")
            offset_map.append(index)
            in_whitespace = True
        else:
            chars.append(char)
            offset_map.append(index)
            in_whitespace = False
    return "".join(chars), offset_map


def _find_all(haystack: str, needle: str) -> list[int]:
    positions: list[int] = []
    start = 0
    while True:
        found = haystack.find(needle, start)
        if found == -1:
            return positions
        positions.append(found)
        start = found + 1


def _line_start_offsets(text: str) -> list[int]:
    starts = [0]
    for index, char in enumerate(text):
        if char == "\n":
            starts.append(index + 1)
    # No entry for a trailing empty "line" after a final newline.
    if text.endswith("\n") and len(starts) > 1:
        starts.pop()
    return starts


def _offset_to_line(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


# ── section mapping ─────────────────────────────────────────────────


def _flatten_sections(sections) -> list[tuple[str, str, int, int, int]]:
    """Flatten the section tree to (id, title, start_line, end_line, level).

    Section line ranges from ingestion are 0-based; convert to the 1-based
    convention anchors use.
    """
    flat: list[tuple[str, str, int, int, int]] = []

    def walk(items) -> None:
        for section in items:
            flat.append(
                (
                    section.id,
                    section.title,
                    section.start_line + 1,
                    section.end_line + 1,
                    section.level,
                )
            )
            walk(section.children or [])

    walk(sections)
    return flat


def _attach_section(
    finding: UnifiedFinding,
    flat_sections: list[tuple[str, str, int, int, int]],
) -> None:
    line = finding.anchor.line_number
    if line is None:
        return
    containing = [s for s in flat_sections if s[2] <= line <= s[3]]
    if not containing:
        return
    # Deepest (highest level), then tightest range.
    best = max(containing, key=lambda s: (s[4], -(s[3] - s[2])))
    finding.anchor.section_id = best[0]
    finding.anchor.section_title = best[1]


def _document_order_key(finding: UnifiedFinding) -> tuple[int, int, int]:
    anchor = finding.anchor
    if anchor.start_offset is None:
        return (1, 0, severity_rank(finding.severity))
    return (0, anchor.start_offset, severity_rank(finding.severity))
