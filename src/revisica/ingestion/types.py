"""Core data types for the ingestion layer."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ParsedImage:
    """A binary image asset produced alongside parsed Markdown.

    ``relative_path`` matches the path used in the markdown's ``![](...)``
    references, rooted at the document's own directory (e.g.
    ``"images/<sha>.jpg"`` for MinerU output). ``data`` is the raw image
    bytes; the storage layer writes them to ``<parsed_doc_dir>/<relative_path>``
    so the renderer can resolve them via the API.
    """

    relative_path: str
    data: bytes


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
