"""Normalize raw Markdown from any parser into a RevisicaDocument."""

from __future__ import annotations

import re
from pathlib import Path

from .types import DocumentMetadata, DocumentSection, RevisicaDocument

# ── section extraction ──────────────────────────────────────────────

_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)


def _extract_sections(markdown: str) -> list[DocumentSection]:
    """Build a flat list of sections from Markdown headings.

    Each section spans from its heading to the next heading of the same
    or higher level (or end-of-file).
    """
    lines = markdown.split("\n")
    headings: list[tuple[int, int, str]] = []  # (line_number, level, title)

    for line_number, line in enumerate(lines):
        match = _HEADING_RE.match(line)
        if match:
            level = len(match.group(1))
            title = match.group(2).strip()
            headings.append((line_number, level, title))

    if not headings:
        return []

    sections: list[DocumentSection] = []
    for index, (start_line, level, title) in enumerate(headings):
        if index + 1 < len(headings):
            end_line = headings[index + 1][0] - 1
        else:
            end_line = len(lines) - 1

        content = "\n".join(lines[start_line:end_line + 1])
        section_id = _make_section_id(index, level, title)

        sections.append(DocumentSection(
            id=section_id,
            title=title,
            level=level,
            start_line=start_line,
            end_line=end_line,
            content=content,
            children=[],
        ))

    return _nest_sections(sections)


def _make_section_id(index: int, level: int, title: str) -> str:
    """Generate a stable section ID from index and title."""
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    if not slug:
        slug = "section"
    return f"sec-{index + 1}-{slug[:40]}"


def _nest_sections(flat_sections: list[DocumentSection]) -> list[DocumentSection]:
    """Convert a flat section list into a nested tree based on heading level."""
    if not flat_sections:
        return []

    root_sections: list[DocumentSection] = []
    stack: list[DocumentSection] = []

    for section in flat_sections:
        while stack and stack[-1].level >= section.level:
            stack.pop()

        if stack:
            stack[-1].children.append(section)
        else:
            root_sections.append(section)

        stack.append(section)

    return root_sections


# ── metadata extraction ─────────────────────────────────────────────

_TITLE_RE = re.compile(r"^#\s+(.+)$", re.MULTILINE)
_AUTHOR_RE = re.compile(
    r"(?:authors?|by)\s*[:\-]\s*(.+)",
    re.IGNORECASE,
)


def _extract_metadata(markdown: str) -> DocumentMetadata:
    """Best-effort metadata extraction from Markdown content.

    Handles both plain Markdown (from tex-basic) and Pandoc output
    which puts title/authors/abstract in YAML frontmatter.
    """
    title = ""
    authors: list[str] = []
    abstract = ""

    # Try YAML frontmatter first (Pandoc --standalone output)
    fm = _extract_yaml_frontmatter(markdown)
    if fm:
        title = fm.get("title", "")
        abstract = fm.get("abstract", "")
        raw_authors = fm.get("author", [])
        if isinstance(raw_authors, list):
            authors = [a for a in raw_authors if isinstance(a, str) and a.strip()]
        elif isinstance(raw_authors, str):
            authors = [a.strip() for a in re.split(r"[,;]|(?:\band\b)", raw_authors) if a.strip()]

    # Fallback: extract from Markdown body
    if not title:
        title_match = _TITLE_RE.search(markdown)
        if title_match:
            title = title_match.group(1).strip()

    if not authors:
        author_match = _AUTHOR_RE.search(markdown[:2000])
        if author_match:
            raw = author_match.group(1)
            authors = [a.strip() for a in re.split(r"[,;]|(?:\band\b)", raw) if a.strip()]

    if not abstract:
        abstract_markers = ["## Abstract", "### Abstract", "**Abstract**", "\\begin{abstract}"]
        lower_markdown = markdown.lower()
        for marker in abstract_markers:
            position = lower_markdown.find(marker.lower())
            if position >= 0:
                start = position + len(marker)
                end = min(start + 2000, len(markdown))
                remaining = markdown[start:end].strip()
                next_heading = _HEADING_RE.search(remaining)
                if next_heading:
                    abstract = remaining[:next_heading.start()].strip()
                else:
                    abstract = remaining[:500].strip()
                break

    return DocumentMetadata(title=title, authors=authors, abstract=abstract)


def _extract_yaml_frontmatter(markdown: str) -> dict | None:
    """Parse YAML frontmatter from Pandoc --standalone output."""
    if not markdown.startswith("---"):
        return None
    end = markdown.find("\n---", 3)
    if end < 0:
        end = markdown.find("\n...", 3)
    if end < 0:
        return None

    yaml_block = markdown[4:end]
    # Lightweight YAML parsing — handles the simple key: value and
    # key:\n- item patterns that Pandoc produces. No PyYAML dependency.
    result: dict = {}
    current_key = ""
    current_value = ""
    list_items: list[str] = []
    in_list = False
    in_multiline = False

    for line in yaml_block.split("\n"):
        stripped = line.strip()
        if not stripped:
            if in_multiline:
                current_value += "\n"
            continue

        # List item
        if line.startswith("- ") and in_list:
            list_items.append(line[2:].strip())
            continue

        # New key
        key_match = re.match(r"^([a-z_-]+)\s*:\s*(.*)", line)
        if key_match:
            # Save previous key
            if current_key:
                if in_list:
                    result[current_key] = list_items
                else:
                    result[current_key] = current_value.strip()

            current_key = key_match.group(1)
            val = key_match.group(2).strip()
            in_list = False
            in_multiline = False
            current_value = ""
            list_items = []

            if val == "|":
                in_multiline = True
            elif val == "" or val == "-":
                in_list = True
                if val == "-":
                    # Inline first item not expected from pandoc, but handle it
                    pass
            else:
                current_value = val
        elif in_multiline:
            current_value += line.strip() + " "
        elif in_list and line.startswith("- "):
            list_items.append(line[2:].strip())

    # Save last key
    if current_key:
        if in_list:
            result[current_key] = list_items
        else:
            result[current_key] = current_value.strip()

    return result if result else None


# ── public API ──────────────────────────────────────────────────────


def normalize_to_document(
    raw_markdown: str,
    source_path: str,
    parser_used: str,
) -> RevisicaDocument:
    """Normalize raw Markdown from any parser into a RevisicaDocument."""
    sections = _extract_sections(raw_markdown)
    metadata = _extract_metadata(raw_markdown)

    return RevisicaDocument(
        source_path=source_path,
        parser_used=parser_used,
        markdown=raw_markdown,
        sections=sections,
        metadata=metadata,
    )
