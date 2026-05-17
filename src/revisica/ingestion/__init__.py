"""Ingestion layer: PDF/tex → RevisicaDocument."""

from .normalize import normalize_to_document
from .registry import parse_document, parse_document_with_assets
from .types import DocumentMetadata, DocumentSection, ParsedImage, RevisicaDocument

__all__ = [
    "DocumentMetadata",
    "DocumentSection",
    "ParsedImage",
    "RevisicaDocument",
    "normalize_to_document",
    "parse_document",
    "parse_document_with_assets",
]
