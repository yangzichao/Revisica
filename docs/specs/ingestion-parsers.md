# Ingestion Parsers Spec

**Status:** implementing
**Date:** 2026-04-12

## Problem

Revisica currently only handles `.tex` input (via `tex_parser` and `pandoc_parser`).
Users also need to review papers distributed as PDFs or already-converted Markdown/MMD files.
The ingestion layer must support multiple input formats while producing a single, clean intermediate representation.

## Design

All parsers share one contract:

```
any input file → parser.parse() → raw Markdown (with LaTeX math in $..$ / $$..$$) → normalize_to_document() → RevisicaDocument
```

```
.tex  ──→ tex_parser / pandoc ──┐
.md   ──→ markdown_parser     ──┤
.mmd  ──→ markdown_parser     ──┼──→ normalize_to_document() ──→ RevisicaDocument
.pdf  ──→ mineru_parser       ──┤
.pdf  ──→ mathpix_parser      ──┘
```

The downstream pipeline (writing lane, math lane) only sees `RevisicaDocument`.
Parser choice is transparent to all review logic.

### New parsers

| Parser | File | Input | Dependency | Cost |
|--------|------|-------|-----------|------|
| `markdown` | `markdown_parser.py` | `.md`, `.mmd` | None | Free |
| `mineru` | `mineru_parser.py` | `.pdf` | `magic-pdf` (pip), GPU/MPS | Free |
| `mathpix` | `mathpix_parser.py` | `.pdf`, images | Mathpix API key | ~$0.01/page |

### Parser priority (auto-detection order)

For `.tex`: Pandoc > tex-basic
For `.pdf`: Mathpix (if API key set) > MinerU (if installed) > Marker (fallback)
For `.md`/`.mmd`: markdown (always available)

### Markdown parser (`markdown_parser.py`)

- Handles `.md` and `.mmd` extensions
- Implementation: `path.read_text(encoding="utf-8")`
- Always available (no dependencies)
- This is the simplest parser — MMD is just Markdown with LaTeX math, which is exactly our intermediate format

### MinerU parser (`mineru_parser.py`)

- Handles `.pdf`
- Calls `magic-pdf` Python API to convert PDF → Markdown
- `is_available()` checks that `magic_pdf` is importable
- Output: Markdown with LaTeX math blocks preserved

### Mathpix parser (`mathpix_parser.py`)

- Handles `.pdf` and image files (`.png`, `.jpg`, `.jpeg`)
- Calls Mathpix API (`POST https://api.mathpix.com/v3/pdf` for PDFs, `/v3/text` for images)
- `is_available()` checks `MATHPIX_APP_ID` and `MATHPIX_APP_KEY` env vars
- Output: MMD (= Markdown with LaTeX math)

## Implementation Plan

1. Create `markdown_parser.py` — trivial passthrough
2. Create `mineru_parser.py` — wraps `magic-pdf` API
3. Create `mathpix_parser.py` — wraps Mathpix REST API
4. Update `registry.py` to include markdown parser in auto-detection
5. Add `tests/test_ingestion.py` with unit tests (skip Mathpix, needs API key)

## Acceptance Criteria

- `revisica review paper.md` works end-to-end
- `revisica review paper.mmd` works end-to-end
- `parse_document("paper.pdf", parser="mineru")` returns a valid `RevisicaDocument` (when magic-pdf installed)
- `parse_document("paper.pdf", parser="mathpix")` returns a valid `RevisicaDocument` (when API key set)
- All parsers produce the same `RevisicaDocument` structure regardless of input format
- Tests pass: `pytest tests/test_ingestion.py`
