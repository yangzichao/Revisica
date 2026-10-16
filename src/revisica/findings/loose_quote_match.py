"""Loose quote matching for reviewer quotes that do not match verbatim.

Reviewers often quote the document in ways a whitespace-insensitive
search still misses:

- stitching passages with an ellipsis
  (``$$g(x) = \\frac{1}{x-1}.$$ ... This function is continuous ...``);
- wrapping the quoted text in labels or quote marks
  (``Intro: "We will prove ..." / Conclusion: "We have shown ..."``);
- re-spacing LaTeX (``\\int_{0}^{1} x^{2}\\,dx`` for the parser's
  ``\\int_ {0} ^ {1} x ^ {2} d x``) or dropping its math delimiters
  (``Therefore \\int_0^1 ...`` for ``Therefore $$\\int_0^1 ...$$``).

Here both the quote and the document drop all whitespace, LaTeX spacing
commands and math delimiters. The quote is first tried whole, then split
into its verbatim fragments; the first fragment that matches is anchored
and extended over the fragments that follow it closely in the document.
"""

from __future__ import annotations

import re

# A fragment shorter than this (whitespace removed) matches too many places.
MIN_LOOSE_FRAGMENT_LENGTH = 15

# Fragments further apart than this (in document characters), or with a
# section heading between them, are separate passages. Only the first is
# anchored, instead of one span covering everything in between.
MAX_STITCHED_FRAGMENT_GAP = 300

# Backslash commands dropped when loose-normalizing: LaTeX spacing
# (\, \; \: \!) and math delimiters (\[ \] \( \)).
_DROPPED_BACKSLASH_COMMAND_CHARS = frozenset(",;:![]()")
_WRAPPING_QUOTE_CHARS = "\"“”"
# Ellipses, quote marks, " / " and label colons ("Line 17: ...").
_FRAGMENT_SEPARATOR_PATTERN = re.compile(r"\.\.\.|…|[\"“”]| / |:\s|：")
_DISPLAY_MATH_PATTERN = re.compile(r"\$\$.+?\$\$|\\\[.+?\\\]", re.DOTALL)
_MARKDOWN_HEADING_PATTERN = re.compile(r"^#{1,6}\s", re.MULTILINE)


class LooseDocumentIndex:
    """The loose-normalized document, plus a map back to original offsets.

    ``offset_map[i]`` is the offset in the original text of the character at
    position ``i`` of ``loose_text``.
    """

    def __init__(self, document_text: str) -> None:
        self.document_text = document_text
        self.loose_text, self.offset_map = loose_normalize_with_offset_map(document_text)

    def find_all(self, loose_needle: str) -> list[int]:
        positions: list[int] = []
        start = 0
        while True:
            found = self.loose_text.find(loose_needle, start)
            if found == -1:
                return positions
            positions.append(found)
            start = found + 1

    def find_next(self, loose_needle: str, start: int) -> int | None:
        found = self.loose_text.find(loose_needle, start)
        return None if found == -1 else found

    def original_span(self, loose_start: int, loose_length: int) -> tuple[int, int]:
        loose_end = loose_start + loose_length - 1
        return self.offset_map[loose_start], self.offset_map[loose_end] + 1

    def original_line(self, loose_position: int) -> int:
        return self.document_text.count("\n", 0, self.offset_map[loose_position]) + 1


def match_quote_loosely(
    quote: str,
    index: LooseDocumentIndex,
    hint_line: int | None,
) -> tuple[int, int] | None:
    """Find the quote in the document; returns original-text char offsets."""
    whole_quote = loose_normalize(quote.strip().strip(_WRAPPING_QUOTE_CHARS))
    if len(whole_quote) >= MIN_LOOSE_FRAGMENT_LENGTH:
        positions = index.find_all(whole_quote)
        if positions:
            start = _pick_nearest_to_line(positions, hint_line, index)
            return index.original_span(start, len(whole_quote))
    return _match_stitched_fragments(quote_fragments(quote), index, hint_line)


def quote_fragments(quote: str) -> list[str]:
    """Verbatim pieces of a reviewer quote, loose-normalized, in quote order.

    Pieces are the display-math blocks plus the text between ellipses,
    quote marks, `` / `` separators and label colons. Pieces too short to
    locate reliably are dropped.
    """
    positioned_pieces: list[tuple[int, str]] = [
        (match.start(), match.group(0)) for match in _DISPLAY_MATH_PATTERN.finditer(quote)
    ]
    piece_start = 0
    for separator in _FRAGMENT_SEPARATOR_PATTERN.finditer(quote):
        positioned_pieces.append((piece_start, quote[piece_start : separator.start()]))
        piece_start = separator.end()
    positioned_pieces.append((piece_start, quote[piece_start:]))

    fragments: list[str] = []
    for _, piece in sorted(positioned_pieces, key=lambda item: item[0]):
        fragment = loose_normalize(piece)
        if len(fragment) >= MIN_LOOSE_FRAGMENT_LENGTH and fragment not in fragments:
            fragments.append(fragment)
    return fragments


def _match_stitched_fragments(
    fragments: list[str],
    index: LooseDocumentIndex,
    hint_line: int | None,
) -> tuple[int, int] | None:
    span_start: int | None = None
    span_end = 0  # loose position just past the anchored text
    for fragment in fragments:
        if span_start is None:
            positions = index.find_all(fragment)
            if positions:
                span_start = _pick_nearest_to_line(positions, hint_line, index)
                span_end = span_start + len(fragment)
            continue
        # Later fragments only extend the span forward, and only when they
        # follow closely; otherwise they are a different passage.
        next_start = index.find_next(fragment, start=span_end)
        if next_start is None:
            continue
        gap_start = index.offset_map[span_end - 1] + 1
        gap_end = index.offset_map[next_start]
        if gap_end - gap_start > MAX_STITCHED_FRAGMENT_GAP or _MARKDOWN_HEADING_PATTERN.search(
            index.document_text, gap_start, gap_end
        ):
            break
        span_end = next_start + len(fragment)
    if span_start is None:
        return None
    return index.original_span(span_start, span_end - span_start)


def _pick_nearest_to_line(
    positions: list[int],
    hint_line: int | None,
    index: LooseDocumentIndex,
) -> int:
    if hint_line is None or len(positions) == 1:
        return positions[0]
    return min(positions, key=lambda position: abs(index.original_line(position) - hint_line))


def loose_normalize(text: str) -> str:
    return loose_normalize_with_offset_map(text)[0]


def loose_normalize_with_offset_map(text: str) -> tuple[str, list[int]]:
    """Drop whitespace, ``$``, and LaTeX spacing / math-delimiter commands."""
    characters: list[str] = []
    offset_map: list[int] = []
    position = 0
    while position < len(text):
        character = text[position]
        if character.isspace() or character == "$":
            position += 1
            continue
        if (
            character == "\\"
            and position + 1 < len(text)
            and text[position + 1] in _DROPPED_BACKSLASH_COMMAND_CHARS
        ):
            position += 2
            continue
        characters.append(character)
        offset_map.append(position)
        position += 1
    return "".join(characters), offset_map
