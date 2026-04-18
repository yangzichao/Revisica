# 0001. Use MinerU as default PDF parser

**Status:** Accepted
**Date:** 2026-04-17
**Commit:** `fc72602`

## Context

The desktop app wires drag-and-drop PDF → `/api/review` → report end-to-end, but with a default install (`pip install .`) no PDF parser registers. Dragging a PDF today raises `"No PDF parser available"` at [registry.py:97-103](../../src/revisica/ingestion/registry.py#L97-L103).

Three candidates were evaluated:

- **MinerU** — local ML-based parser, already implemented at [mineru_parser.py](../../src/revisica/ingestion/mineru_parser.py) but not installed by default.
- **Marker** — alternative local ML parser; [registry.py:48-54](../../src/revisica/ingestion/registry.py#L48-L54) references `MarkerParser` but the module does not exist (silent `ImportError`).
- **Plain-text extraction** (`pypdf` / `pdfminer.six`) — cheap and pure-Python.

The local-first privacy ordering (MinerU > Marker > Mathpix) was already documented in [docs/learning/2026-04-12-ingestion-parsers-design.md](../learning/2026-04-12-ingestion-parsers-design.md).

## Decision

**We will use MinerU as the default PDF parser**, installed into the runtime Python (pyenv 3.12 in dev, bundled Python in distribution). Marker is deferred; plain-text extraction is rejected outright.

Selection criteria, in priority order, that MinerU meets:

1. **Zero code change** — [mineru_parser.py](../../src/revisica/ingestion/mineru_parser.py) already spawns the `mineru` CLI, reads generated Markdown, and plugs into the registry at [registry.py:40-46](../../src/revisica/ingestion/registry.py#L40-L46). Only installation is missing.
2. **Local** — PDFs stay on device, matching the privacy ordering.
3. **Apple Silicon friendly** — MPS-accelerated; the primary dev machine is Mac.
4. **Output compatibility** — produces Markdown with LaTeX math (`$...$` / `$$...$$`), exactly what `normalize_to_document()` expects.
5. **CLI stability** — the `mineru` CLI survives the 1.x → 2.x Python-API churn. Subprocess boundary insulates us from internal breakage.

## Consequences

**Easier:**
- PDF support ships without a single new Python module.
- Math survives ingestion, so the math-review lane continues to function on PDFs.
- Switching local parsers in the future is a registry edit, not a refactor.

**Harder / newly risky:**
- MinerU requires Python `>=3.10,<3.14`. The project's `.venv` is pinned at 3.9.6 for dual-distribution reasons (see [docs/learning/2026-04-11-dual-distribution-provider-mode.md](../learning/2026-04-11-dual-distribution-provider-mode.md)). The desktop app already falls back to pyenv `python3` when `.venv` is too old — MinerU must be installed into *that* Python.
- First parse downloads ~7 HuggingFace model files (~1 GB) and pulls ~2 GB of torch/transformers via `mineru[core]`. This inflates any future all-in-one bundle.
- `revisica bootstrap` does not install MinerU; users wanting PDF support must `pip install 'mineru[core]'` manually. The error message at [registry.py:97-103](../../src/revisica/ingestion/registry.py#L97-L103) already tells them.
- The silent `ImportError` for `MarkerParser` is a **known latent bug** left in place. Whoever next touches the ingestion registry should decide: implement Marker or delete the branch.

Install-time gotchas and verification evidence: see [docs/learning/2026-04-17-mineru-install-gotchas.md](../learning/2026-04-17-mineru-install-gotchas.md).

## Rejected alternatives

**Marker — deferred, not rejected.** No unique win over MinerU on our target hardware (its one advantage, "no GPU needed," only matters for CPU-only Linux boxes we do not run today). Writing a correct parser + tests is ~1–2 hours even following the MinerU shape, and then we own two local parsers. Revisit if benchmark runners move to CPU-only hardware, or if users report MinerU install failures on Intel/no-MPS machines.

**Plain-text (`pypdf` / `pdfminer.six`) — rejected outright.**
- Destroys math: glyph-level extraction produces garbage (`p ( x ; θ )` with broken spacing) or drops equations that use embedded fonts.
- Breaks the math-review lane, which depends on `$...$` / `$$...$$` delimiters surviving ingestion.
- Trust-destroying failure mode: a successful-looking PDF review that silently skipped all the math is worse than a hard failure at ingestion.
- Not worth keeping as an opt-in toggle; it creates a "why is my math review empty?" support class we do not want.

**Mathpix remains available as the cloud escape hatch** for users who cannot install MinerU (no MPS, locked-down corporate machine). Activated by `MATHPIX_APP_ID` / `MATHPIX_APP_KEY` env vars; opt-in and never auto-selected, per the privacy ordering.
