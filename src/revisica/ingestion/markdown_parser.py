"""Passthrough parser for Markdown and Mathpix Markdown (.mmd) files.

These formats are already in the intermediate representation expected by
:func:`normalize_to_document`, so no conversion is needed.
"""

from __future__ import annotations

from pathlib import Path

from .base import BaseParser

_SUPPORTED_EXTENSIONS = {".md", ".mmd", ".markdown"}


class MarkdownParser(BaseParser):
    """Read Markdown / MMD files as-is."""

    name = "markdown"

    def can_handle(self, path: Path) -> bool:
        return path.suffix.lower() in _SUPPORTED_EXTENSIONS

    @classmethod
    def is_available(cls) -> bool:
        return True  # No external dependencies

    def parse(self, path: Path) -> str:
        return path.read_text(encoding="utf-8")
