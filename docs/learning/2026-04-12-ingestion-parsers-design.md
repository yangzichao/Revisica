# Learning: Multi-Format Ingestion — One Intermediate Format

**Date:** 2026-04-12
**Commit:** (pending — this commit)
**Context:** Implemented three new parsers (markdown, MinerU, Mathpix) to support PDF and Markdown/MMD input alongside the existing LaTeX path.

## The Observation

All three PDF-to-text tools (Mathpix, MinerU, Marker) and the Mathpix Markdown (.mmd) format produce the same thing: **Markdown with LaTeX math in `$...$` / `$$...$$`**. This is not a coincidence — it's the natural intermediate representation for academic papers because Markdown handles structure and LaTeX handles math. No other format does both well.

The `BaseParser` contract (`parse() → str` returning raw Markdown) was already correct. Adding three new input formats required zero changes to `normalize_to_document()` or any downstream code.

## The Lesson

**"Markdown + LaTeX math" is the lingua franca for academic document interchange.**

- MMD (Mathpix Markdown) adds no syntax beyond standard Markdown — it's a branding distinction, not a format distinction.
- MinerU (magic-pdf) outputs Markdown with LaTeX math natively. So does Marker.
- The `.tex` → Markdown conversion (via Pandoc or regex) preserves math in `$`/`$$` delimiters.
- Therefore: one normalize function handles all sources.

**MinerU has two incompatible Python APIs across major versions:**
- magic-pdf 1.x: synchronous in-process `UNIPipe` pipeline. Direct, reliable.
- MinerU 2.x: server-mediated `api_client`. No exposed synchronous pipe API.
- Lesson: support both backends with auto-detection, prefer 1.x when available.

**Parser isolation pays off immediately.** Each parser is a single file with no cross-dependencies. Tests for the markdown parser and normalize layer run in 0.05s with no external services. This is the first pytest suite in the project — 24 tests, all passing.

## Architecture Implications

1. **Ingestion is no longer an island** (addressing item #3 from the 2026-04-11 architecture debt observation). Three new parsers are wired through the existing registry and produce `RevisicaDocument`. The next step is having the review pipeline consume `RevisicaDocument` instead of reading raw `.tex`.

2. **The parser registry auto-detection order matters for PDF:**
   Mathpix (highest math fidelity, paid) > MinerU (open source, GPU) > Marker (no GPU, lower math quality).
   For `.tex`: Pandoc > tex-basic. For `.md`/`.mmd`: always available.

3. **Test infrastructure now exists.** `tests/` directory with pytest. Future modules can follow the same pattern. The ingestion tests serve as a template: test imports, `can_handle()`, actual parsing with fixtures, and registry integration.
