# Learning: Multi-Format Ingestion — One Intermediate Format

**Date:** 2026-04-12
**Commits:** `e7bd1e6`..`92a7d47` (5 commits)
**Context:** Implemented three new parsers (markdown, MinerU, Mathpix) to support PDF and Markdown/MMD input alongside the existing LaTeX path. Then simplified, fixed privacy ordering, added mock tests, and updated the API.

## The Observation

All three PDF-to-text tools (Mathpix, MinerU, Marker) and the Mathpix Markdown (.mmd) format produce the same thing: **Markdown with LaTeX math in `$...$` / `$$...$$`**. This is not a coincidence — it's the natural intermediate representation for academic papers because Markdown handles structure and LaTeX handles math. No other format does both well.

The `BaseParser` contract (`parse() → str` returning raw Markdown) was already correct. Adding three new input formats required zero changes to `normalize_to_document()` or any downstream code.

## The Lessons

**"Markdown + LaTeX math" is the lingua franca for academic document interchange.**

- MMD (Mathpix Markdown) adds no syntax beyond standard Markdown — it's a branding distinction, not a format distinction.
- MinerU (magic-pdf) outputs Markdown with LaTeX math natively. So does Marker.
- The `.tex` → Markdown conversion (via Pandoc or regex) preserves math in `$`/`$$` delimiters.
- Therefore: one normalize function handles all sources.

**MinerU: just use the CLI.** The Python API changed incompatibly between 1.x (`UNIPipe` in-process) and 2.x (server-mediated `api_client`). But the `mineru` CLI works across both versions. Treating it as a subprocess (like Pandoc) avoids coupling to either internal API. Don't over-engineer version detection when a stable CLI exists.

**Local-first for privacy.** Auto-detection order for PDF: MinerU (local) > Marker (local) > Mathpix (cloud). Cloud parsers should never be selected automatically — uploading a user's document to a third-party service without explicit opt-in is a privacy violation. Use `parser="mathpix"` explicitly.

**Parser isolation pays off immediately.** Each parser is a single file with no cross-dependencies. Tests for the markdown parser and normalize layer run in 0.03s with no external services. 29 tests, all passing. Mock tests for MinerU use monkeypatch scoped to the module (`mp.shutil`, `mp.subprocess`) to avoid global test pollution.

## Architecture Implications

1. **Ingestion is no longer an island** (addressing item #3 from the 2026-04-11 architecture debt observation). Three new parsers are wired through the existing registry and produce `RevisicaDocument`. The next step is having the review pipeline consume `RevisicaDocument` instead of reading raw `.tex`.

2. **The parser registry auto-detection order matters for PDF:**
   MinerU (local, GPU) > Marker (local, no GPU) > Mathpix (cloud, opt-in).
   For `.tex`: Pandoc > tex-basic. For `.md`/`.mmd`/`.markdown`: always available.

3. **The `/api/ingest` endpoint returns both full markdown and per-section content.** This supports a standalone document viewer UI without coupling to the review pipeline. The `_flatten_sections()` helper linearizes the nested section tree for the API response.

4. **Test infrastructure now exists.** `tests/` directory with pytest, 29 tests. Future modules can follow the same pattern: test imports, `can_handle()`, actual parsing with fixtures, and registry integration. Monkeypatch should always target module-level references, not globals.
