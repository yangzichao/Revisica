# Ingestion Parsers Spec

**Status:** done
**Date:** 2026-04-12
**Commits:** `e7bd1e6`..`92a7d47`

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
| `mineru` | `mineru_parser.py` | `.pdf` | `mineru` CLI (pip install mineru), GPU/MPS | Free |
| `mathpix` | `mathpix_parser.py` | `.pdf`, images | Mathpix API key | ~$0.01/page |

### Parser priority (auto-detection order)

For `.tex`: Pandoc > tex-basic
For `.pdf`: MinerU (local, GPU) > Marker (local, no GPU) > Mathpix (cloud, opt-in)
For `.md`/`.mmd`/`.markdown`: markdown (always available)

Local parsers are preferred over cloud to avoid silently uploading documents to third-party services. Use `parser="mathpix"` explicitly for cloud OCR.

### Markdown parser (`markdown_parser.py`)

- Handles `.md` and `.mmd` extensions
- Implementation: `path.read_text(encoding="utf-8")`
- Always available (no dependencies)
- This is the simplest parser — MMD is just Markdown with LaTeX math, which is exactly our intermediate format

### MinerU parser (`mineru_parser.py`)

- Handles `.pdf`
- Calls `mineru` CLI as subprocess (same pattern as `pandoc_parser.py`)
- `is_available()` checks `shutil.which("mineru")`
- Output layout: `<tmpdir>/<stem>/<stem>.md`
- Output: Markdown with LaTeX math blocks preserved
- CLI-only: avoids coupling to incompatible Python APIs across MinerU 1.x/2.x

### Mathpix parser (`mathpix_parser.py`)

- Handles `.pdf` and image files (`.png`, `.jpg`, `.jpeg`)
- Calls Mathpix API (`POST https://api.mathpix.com/v3/pdf` for PDFs, `/v3/text` for images)
- `is_available()` checks `MATHPIX_APP_ID` and `MATHPIX_APP_KEY` env vars
- Output: MMD (= Markdown with LaTeX math)

## Implementation Plan

1. [x] Create `markdown_parser.py` — trivial passthrough
2. [x] Create `mineru_parser.py` — CLI subprocess wrapper
3. [x] Create `mathpix_parser.py` — wraps Mathpix REST API
4. [x] Update `registry.py` — local-first PDF parser ordering, all formats in auto-detection
5. [x] Add `tests/test_ingestion.py` — 29 tests (markdown, normalize, registry, MinerU mock, Mathpix import)
6. [x] Update `/api/ingest` endpoint — returns full markdown + per-section content
7. [x] Add fixture: `tests/fixtures/mineru_output_sample.md` (realistic econ paper for MinerU mock tests)

## Acceptance Criteria

- [x] `parse_document("paper.md")` and `parse_document("paper.mmd")` return valid `RevisicaDocument`
- [x] `parse_document("paper.pdf", parser="mineru")` returns a valid `RevisicaDocument` (mocked in tests)
- [x] `parse_document("paper.pdf", parser="mathpix")` returns a valid `RevisicaDocument` (when API key set)
- [x] All parsers produce the same `RevisicaDocument` structure regardless of input format
- [x] Auto-detection prefers local parsers over cloud for PDF
- [x] Tests pass: `pytest tests/test_ingestion.py` — 29/29 passing
