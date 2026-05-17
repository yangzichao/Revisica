"""Parser registry with auto-detection."""

from __future__ import annotations

import logging
from pathlib import Path

from .base import BaseParser
from .normalize import normalize_to_document
from .types import ParsedImage, RevisicaDocument

logger = logging.getLogger(__name__)


def _get_available_parsers() -> list[BaseParser]:
    """Lazily discover available parsers."""
    parsers: list[BaseParser] = []

    # Pandoc — preferred for .tex
    try:
        from .pandoc_parser import PandocParser
        if PandocParser.is_available():
            parsers.append(PandocParser())
    except ImportError:
        pass

    # tex-basic — fallback for .tex when Pandoc is not installed
    try:
        from .tex_parser import TexParser
        if TexParser.is_available():
            parsers.append(TexParser())
    except ImportError:
        pass

    # ── PDF parsers: local-first, cloud opt-in ──
    # Auto-detection prefers local parsers to avoid silently uploading
    # documents to third-party services.  Use parser="mathpix" explicitly
    # for cloud OCR.

    # MinerU — local, open source (preferred for PDF)
    try:
        from .mineru_parser import MineruParser
        if MineruParser.is_available():
            parsers.append(MineruParser())
    except ImportError:
        pass

    # Marker — local fallback (no GPU needed)
    try:
        from .marker_parser import MarkerParser
        if MarkerParser.is_available():
            parsers.append(MarkerParser())
    except ImportError:
        pass

    # Mathpix — cloud API, registered last for PDF so local parsers
    # win in auto-detection.  Still selectable via parser="mathpix".
    try:
        from .mathpix_parser import MathpixParser
        if MathpixParser.is_available():
            parsers.append(MathpixParser())
    except ImportError:
        pass

    # Markdown / MMD — passthrough (always available, last in list
    # so it never shadows .pdf parsers in auto-detection)
    from .markdown_parser import MarkdownParser
    parsers.append(MarkdownParser())

    return parsers


def _select_parser(path: Path, parser_name: str) -> BaseParser:
    """Select a parser by name or auto-detect the best one for the file."""
    available_parsers = _get_available_parsers()

    if parser_name != "auto":
        for parser in available_parsers:
            if parser.name == parser_name:
                if not parser.can_handle(path):
                    raise ValueError(
                        f"Parser '{parser_name}' cannot handle {path.suffix} files."
                    )
                return parser
        available_names = [p.name for p in available_parsers]
        raise ValueError(
            f"Parser '{parser_name}' not available. "
            f"Available: {available_names or 'none'}"
        )

    # Auto-detect: find the best parser that can handle this file
    for parser in available_parsers:
        if parser.can_handle(path):
            return parser

    suffix = path.suffix.lower()
    if suffix == ".pdf":
        raise RuntimeError(
            "No PDF parser available. Install one of:\n"
            "  - pip install 'mineru[all]'   (MinerU — auto-selects MLX on Mac, vLLM on Linux, lmdeploy on Windows)\n"
            "  - pip install marker-pdf      (Marker, local, no GPU needed)\n"
            "  - Set MATHPIX_APP_ID + MATHPIX_APP_KEY for Mathpix cloud API"
        )
    if suffix == ".tex":
        raise RuntimeError(
            "No .tex parser available. This should not happen — "
            "the built-in tex-basic parser should always be available."
        )
    if suffix in (".md", ".mmd", ".markdown"):
        raise RuntimeError(
            "No Markdown parser available. This should not happen — "
            "the built-in markdown parser should always be available."
        )
    raise RuntimeError(f"No parser can handle {suffix} files.")


def parse_document(
    path: str | Path,
    parser: str = "auto",
    mineru_backend: str | None = None,
    mineru_progress_callback=None,
) -> RevisicaDocument:
    """Parse a file into a RevisicaDocument.

    Args:
        path: Path to the input file (.tex, .md, .mmd, or .pdf).
        parser: Parser name ("pandoc", "tex-basic", "markdown",
                "mineru", "marker", "mathpix") or "auto" to select
                the best available.  Auto prefers local parsers.
        mineru_backend: Optional MinerU sub-backend ("vlm", "pipeline",
                "hybrid", "auto"). Only used when the chosen parser is
                MinerU. ``None`` keeps the parser's default ("vlm").
        mineru_progress_callback: Optional ``MineruChunkProgress`` callback
                invoked on each chunk transition when MinerU auto-splits a
                large PDF. Ignored for other parsers.

    Returns:
        A normalized RevisicaDocument.

    See also :func:`parse_document_with_assets` for callers (the desktop
    parse worker) that need the image bytes alongside the document.
    """
    document, _ = parse_document_with_assets(
        path,
        parser=parser,
        mineru_backend=mineru_backend,
        mineru_progress_callback=mineru_progress_callback,
    )
    return document


def parse_document_with_assets(
    path: str | Path,
    parser: str = "auto",
    mineru_backend: str | None = None,
    mineru_progress_callback=None,
) -> tuple[RevisicaDocument, list[ParsedImage]]:
    """Parse a file into a ``(RevisicaDocument, images)`` pair.

    Same dispatch + fallback semantics as :func:`parse_document`, but
    also returns the binary image assets produced by the parser (only
    MinerU emits any today). Callers that don't need images should use
    :func:`parse_document` instead — both go through the same
    ``parse_with_assets`` codepath under the hood.
    """
    file_path = Path(path).expanduser().resolve()
    if not file_path.exists():
        raise FileNotFoundError(f"Input file does not exist: {file_path}")
    if not file_path.is_file():
        raise IsADirectoryError(f"Input path is not a file: {file_path}")

    selected_parser = _select_parser(file_path, parser)

    if selected_parser.name == "mineru" and (
        mineru_backend or mineru_progress_callback is not None
    ):
        from .mineru_parser import MineruParser
        selected_parser = MineruParser(
            backend=mineru_backend,
            progress_callback=mineru_progress_callback,
        )

    try:
        raw_markdown, images = selected_parser.parse_with_assets(file_path)
    except Exception:
        if parser != "auto":
            raise  # User explicitly chose this parser — don't silently fall back
        # Auto mode: try next available parser
        fallback = _find_fallback(file_path, exclude=selected_parser.name)
        if fallback is None:
            raise
        logger.warning(
            "%s failed on %s, falling back to %s",
            selected_parser.name, file_path.name, fallback.name,
        )
        raw_markdown, images = fallback.parse_with_assets(file_path)
        selected_parser = fallback

    document = normalize_to_document(
        raw_markdown=raw_markdown,
        source_path=str(file_path),
        parser_used=selected_parser.name,
    )
    return document, images


def _find_fallback(path: Path, exclude: str) -> BaseParser | None:
    """Find the next parser that can handle the file, skipping *exclude*."""
    for p in _get_available_parsers():
        if p.name != exclude and p.can_handle(path):
            return p
    return None
