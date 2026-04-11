"""Ingestion layer: PDF/tex → RevisicaDocument."""

from .normalize import normalize_to_document
from .registry import parse_document
from .types import DocumentMetadata, DocumentSection, RevisicaDocument

__all__ = [
    "DocumentMetadata",
    "DocumentSection",
    "RevisicaDocument",
    "normalize_to_document",
    "parse_document",
]
