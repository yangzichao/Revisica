"""Core data types for the ingestion layer."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class DocumentMetadata:
    """Extracted metadata from a parsed document."""

    title: str = ""
    authors: list[str] = field(default_factory=list)
    abstract: str = ""


@dataclass
class DocumentSection:
    """A section in a parsed document, forming a tree structure.

    Each section has a stable ``id`` (e.g. "sec-3", "sec-3.1") that is
    used to anchor review findings and enable Focus-mode deep dives.
    """

    id: str
    title: str
    level: int
    start_line: int
    end_line: int
    content: str
    children: list[DocumentSection] = field(default_factory=list)


@dataclass
class RevisicaDocument:
    """Standardized intermediate format for a parsed academic paper.

    This is the single representation consumed by the review pipeline
    (writing lane, math lane) and by the desktop app renderer.  All
    parsers (Mathpix, MinerU, Marker, Pandoc) normalize their output
    to this format via :func:`normalize_to_document`.
    """

    source_path: str
    parser_used: str
    markdown: str
    sections: list[DocumentSection] = field(default_factory=list)
    metadata: DocumentMetadata = field(default_factory=DocumentMetadata)
