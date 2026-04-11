"""Abstract base class for document parsers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path


class BaseParser(ABC):
    """Convert a file (PDF or .tex) to raw Markdown with LaTeX math.

    Subclasses handle one input format or service (Pandoc, Mathpix, etc.).
    The returned Markdown is then passed through :func:`normalize_to_document`
    to produce a :class:`RevisicaDocument`.
    """

    name: str = ""

    @abstractmethod
    def can_handle(self, path: Path) -> bool:
        """Return True if this parser can process the given file."""

    @abstractmethod
    def parse(self, path: Path) -> str:
        """Parse *path* and return raw Markdown (with LaTeX math blocks)."""

    @classmethod
    def is_available(cls) -> bool:
        """Return True if this parser's dependencies are satisfied."""
        return True
