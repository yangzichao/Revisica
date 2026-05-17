"""Abstract base class for document parsers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from .types import ParsedImage


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

    def parse_with_assets(self, path: Path) -> tuple[str, list[ParsedImage]]:
        """Parse *path*, returning Markdown plus any binary image assets.

        The default implementation delegates to :meth:`parse` and returns
        an empty asset list — parsers that emit no local image files
        (Mathpix, Pandoc, Markdown passthrough) inherit this for free.
        Parsers that produce images alongside their markdown (e.g. MinerU)
        override this and capture them before their working directory is
        cleaned up.
        """
        return self.parse(path), []

    @classmethod
    def is_available(cls) -> bool:
        """Return True if this parser's dependencies are satisfied."""
        return True
