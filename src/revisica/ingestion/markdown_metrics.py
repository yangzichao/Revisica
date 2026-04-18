"""Pure metric functions over raw Markdown output.

These helpers intentionally bypass ``normalize_to_document`` so that
benchmarks can compare parser outputs apples-to-apples without any single
parser benefiting from normalization heuristics.

All functions accept a raw Markdown string and return primitive values
(int / list[str] / str). They have no external dependencies and no IO.
"""

from __future__ import annotations

import re


# ── math counting ──────────────────────────────────────────────────────

_INLINE_DOLLAR_RE = re.compile(r"(?<!\$)\$(?!\$)(.+?)(?<!\$)\$(?!\$)", re.DOTALL)
_DISPLAY_DOLLAR_RE = re.compile(r"\$\$")
_INLINE_PAREN_RE = re.compile(r"\\\((.+?)\\\)", re.DOTALL)
_DISPLAY_BRACKET_RE = re.compile(r"\\\[(.+?)\\\]", re.DOTALL)


def count_inline_math(markdown: str) -> int:
    """Count inline math spans.

    Accepts both ``$...$`` and ``\\(...\\)`` delimiters. Double-dollar
    display math is excluded via negative lookaround.
    """
    dollar_count = len(_INLINE_DOLLAR_RE.findall(markdown))
    paren_count = len(_INLINE_PAREN_RE.findall(markdown))
    return dollar_count + paren_count


def count_display_math(markdown: str) -> int:
    """Count display math blocks.

    Accepts both ``$$...$$`` and ``\\[...\\]`` delimiters. The ``$$``
    count is the number of delimiter pairs, so each block counts once.
    """
    dollar_pairs = len(_DISPLAY_DOLLAR_RE.findall(markdown)) // 2
    bracket_count = len(_DISPLAY_BRACKET_RE.findall(markdown))
    return dollar_pairs + bracket_count


# ── heading structure ──────────────────────────────────────────────────

_HEADING_LINE_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$", re.MULTILINE)


def count_headings(markdown: str) -> int:
    """Count ATX-style headings (``#`` through ``######``) at line start."""
    return len(_HEADING_LINE_RE.findall(markdown))


def collect_heading_titles(markdown: str) -> list[str]:
    """Return every ATX heading's title text (inner text, no ``#`` marks)."""
    return [match.group(2).strip() for match in _HEADING_LINE_RE.finditer(markdown)]


def dirty_section_titles(markdown: str) -> list[str]:
    """Return heading titles that still contain LaTeX residue (``\\`` or ``{``)."""
    return [title for title in collect_heading_titles(markdown)
            if "\\" in title or "{" in title]


# ── leftover LaTeX command detection ───────────────────────────────────

_LEFTOVER_COMMAND_MARKERS: tuple[str, ...] = (
    "\\title{",
    "\\author{",
    "\\email{",
    "\\affiliation{",
    "\\begin{abstract}",
    "\\vspace{",
    "\\hspace{",
    "\\Huge",
    "\\includegraphics",
    "\\caption{",
    "\\label{",
    "\\bibliographystyle",
    "\\bibliography{",
    "\\bibitem",
)


def detect_leftover_latex_commands(markdown: str) -> list[str]:
    """Return the distinct leftover LaTeX command names found in the output.

    The returned names are command prefixes (``\\label`` rather than
    ``\\label{foo}``) so they can be grouped and reported compactly.
    """
    found: set[str] = set()
    for marker in _LEFTOVER_COMMAND_MARKERS:
        if marker in markdown:
            found.add(marker.split("{")[0])
    return sorted(found)


# ── title / author / abstract extraction (raw, no normalize) ───────────

_YAML_FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n(?:---|\.\.\.)\s*\n", re.DOTALL)
_YAML_TITLE_RE = re.compile(r"^title\s*:\s*(.+)$", re.MULTILINE)
# Blocks end at the next top-level YAML key (alphabetic start of line), not at
# any non-whitespace char — otherwise ``- item`` list entries would terminate
# the block early.
_YAML_AUTHOR_BLOCK_RE = re.compile(
    r"^author\s*:\s*(.*?)(?=^[A-Za-z_]|\Z)", re.MULTILINE | re.DOTALL
)
_YAML_ABSTRACT_BLOCK_RE = re.compile(
    r"^abstract\s*:\s*(.*?)(?=^[A-Za-z_]|\Z)", re.MULTILINE | re.DOTALL
)
_FIRST_H1_RE = re.compile(r"^#\s+(.+?)\s*$", re.MULTILINE)
_TITLE_CLEAN_RE = re.compile(r"[\\{}]")


def extract_title(markdown: str) -> str:
    """Extract a best-effort document title from raw Markdown.

    Prefers a YAML frontmatter ``title:`` field, then falls back to the
    first H1. Returns an empty string if no title can be found.
    """
    frontmatter = _YAML_FRONTMATTER_RE.search(markdown)
    if frontmatter:
        title_match = _YAML_TITLE_RE.search(frontmatter.group(1))
        if title_match:
            return _strip_quotes(title_match.group(1).strip())

    h1_match = _FIRST_H1_RE.search(markdown)
    if h1_match:
        return h1_match.group(1).strip()

    return ""


def extract_authors(markdown: str) -> list[str]:
    """Extract author names from YAML frontmatter or common markdown patterns.

    Returns an empty list if no authors can be confidently extracted.
    """
    frontmatter = _YAML_FRONTMATTER_RE.search(markdown)
    if frontmatter:
        block_match = _YAML_AUTHOR_BLOCK_RE.search(frontmatter.group(1))
        if block_match:
            raw_block = block_match.group(1).strip()
            list_items = [
                line.strip()[2:].strip()
                for line in raw_block.splitlines()
                if line.strip().startswith("- ")
            ]
            if list_items:
                return [_strip_quotes(item) for item in list_items if item]
            if raw_block:
                return _split_author_string(raw_block)

    author_line_match = re.search(
        r"(?im)^\s*(?:authors?|by)\s*[:\-]\s*(.+)$", markdown[:4000]
    )
    if author_line_match:
        return _split_author_string(author_line_match.group(1))

    return []


def extract_abstract(markdown: str, max_chars: int = 2000) -> str:
    """Return the abstract text if present, capped at *max_chars*.

    Recognizes ``## Abstract``/``### Abstract`` headings, ``**Abstract**``
    bold markers, and ``\\begin{abstract}...\\end{abstract}`` fences left
    over from unstripped LaTeX.
    """
    for marker in ("## Abstract", "### Abstract", "**Abstract**", "\\begin{abstract}"):
        position = markdown.lower().find(marker.lower())
        if position < 0:
            continue
        start = position + len(marker)
        remainder = markdown[start : start + max_chars + 200]
        end_match = _HEADING_LINE_RE.search(remainder)
        if end_match:
            abstract = remainder[: end_match.start()]
        else:
            abstract = remainder
        abstract = abstract.replace("\\end{abstract}", "")
        return abstract.strip()[:max_chars]

    frontmatter = _YAML_FRONTMATTER_RE.search(markdown)
    if frontmatter:
        abstract_match = _YAML_ABSTRACT_BLOCK_RE.search(frontmatter.group(1))
        if abstract_match:
            raw_abstract = abstract_match.group(1).strip()
            # YAML folded/literal scalars: ``abstract: |`` or ``abstract: >``
            # put the text on the following indented lines.
            if raw_abstract in ("|", ">"):
                raw_abstract = ""
            if raw_abstract.startswith(("|", ">")):
                raw_abstract = raw_abstract.lstrip("|>").lstrip()
            dedented_lines = [line.strip() for line in raw_abstract.splitlines()]
            joined = " ".join(line for line in dedented_lines if line)
            return joined[:max_chars]

    return ""


# ── helpers ────────────────────────────────────────────────────────────


def _strip_quotes(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
        return value[1:-1]
    return value


def _split_author_string(raw: str) -> list[str]:
    parts = re.split(r"[,;]|\band\b", raw)
    return [_strip_quotes(part.strip()) for part in parts if part.strip()]


# ── normalization for fuzzy comparison ─────────────────────────────────

_PUNCT_RE = re.compile(r"[\[\](){}.,;:!?\"'`—–\-]+")
_WHITESPACE_RE = re.compile(r"\s+")


def normalize_for_comparison(text: str) -> str:
    """Lowercase, strip punctuation, collapse whitespace — for fuzzy match."""
    lowered = text.lower()
    no_latex = _TITLE_CLEAN_RE.sub(" ", lowered)
    no_punct = _PUNCT_RE.sub(" ", no_latex)
    return _WHITESPACE_RE.sub(" ", no_punct).strip()


def tokenize(text: str) -> set[str]:
    """Lowercase word-level token set for Jaccard/F1 computations."""
    normalized = normalize_for_comparison(text)
    return {token for token in normalized.split() if token}
