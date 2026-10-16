"""Pick the text file the writing agents read.

Writing agents receive a file path and open the file with their own tools,
so the lane needs a plain-text file on disk. LaTeX and Markdown sources are
reviewed as-is; anything else (e.g. a PDF) is reviewed through the
normalized markdown that the ingestion step already produced.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..ingestion.types import RevisicaDocument

PLAIN_TEXT_SOURCE_SUFFIXES = frozenset({".tex", ".md", ".mmd", ".markdown"})


def prepare_writing_source(
    source_path: str,
    document: RevisicaDocument | None,
    writing_dir: Path,
) -> str:
    """Return the path the writing lane should review.

    For non-text sources the ingested markdown is written to
    ``<writing_dir>/<stem>.normalized.md``. That is the same text the
    unified findings are anchored against, so writing-lane snippets match.
    """
    source = Path(source_path)
    if source.suffix.lower() in PLAIN_TEXT_SOURCE_SUFFIXES:
        return source_path
    if document is None or not document.markdown.strip():
        raise ValueError(
            f"Cannot run the writing review on '{source.name}': it is not a "
            "plain-text source and ingestion produced no text to review."
        )
    writing_dir.mkdir(parents=True, exist_ok=True)
    normalized_path = writing_dir / f"{source.stem}.normalized.md"
    normalized_path.write_text(document.markdown, encoding="utf-8")
    return str(normalized_path)
