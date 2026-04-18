# Learning: PDF Parser — MinerU as Default, Marker and Plain-Text Rejected

**Date:** 2026-04-17
**Commit:** `fc72602`
**Context:** The desktop app wires drag-and-drop PDF → `/api/review` → report end-to-end, but with a default install (`pip install .`) no PDF parser registers. Dragging a PDF today raises `"No PDF parser available"` at [registry.py:97-103](../../src/revisica/ingestion/registry.py#L97-L103). We evaluated three ways to close the gap and picked one.

## The Decision

**Path A — MinerU — chosen.** Install `mineru` into the project venv; [mineru_parser.py](../../src/revisica/ingestion/mineru_parser.py) is already implemented and will auto-register via the existing registry.

**Path B — Marker — rejected for now.** Deferred until we have a concrete need it uniquely solves.

**Path C — Plain-text (pypdf / pdfminer) — rejected outright.** Incompatible with product value.

## Why MinerU

- **Zero code change.** [mineru_parser.py](../../src/revisica/ingestion/mineru_parser.py) already spawns the `mineru` CLI, reads the generated Markdown, and plugs into the registry at [registry.py:40-46](../../src/revisica/ingestion/registry.py#L40-L46). Installation is the only missing step.
- **Local.** PDFs stay on device — matches the local-first privacy ordering (MinerU > Marker > Mathpix) already documented in the 2026-04-12 ingestion learning.
- **Apple Silicon friendly.** MPS-accelerated; the primary dev machine is Mac.
- **Output quality.** Produces Markdown with LaTeX math in `$...$` / `$$...$$`, which is exactly the intermediate format `normalize_to_document()` already expects.
- **CLI stability.** As noted in the 2026-04-12 learning, the `mineru` CLI survives the 1.x → 2.x Python-API churn. Subprocess boundary insulates us from internal breakage.

## Why Marker was rejected (for now)

- **Missing code.** [registry.py:48-54](../../src/revisica/ingestion/registry.py#L48-L54) references `MarkerParser` but [marker_parser.py](../../src/revisica/ingestion/) does not exist. The `ImportError` is silently swallowed — a latent bug from the 2026-04-12 parser work.
- **Net new effort.** Writing a correct parser + tests is ~1–2 hours even following the MinerU shape, and then we own two local parsers.
- **No unique win over MinerU on our target hardware.** Marker's one advantage is "no GPU needed," which is only relevant if we later need to run on CPU-only Linux boxes (e.g. a headless CI eval worker or a cheap cloud VM). We do not have that requirement today.
- **Future trigger to revisit:** if benchmark runners move to CPU-only hardware, or if users report MinerU install failures (torch / MPS issues) on their machines, implement Marker as the CPU fallback. At that point, also delete or fix the silent ImportError.

## Why Plain-text was rejected outright

- **Destroys math.** `pypdf` / `pdfminer.six` extract glyph runs, not semantics. Equations degrade to garbage (`p ( x ; θ )` with broken spacing) or vanish entirely when rendered via embedded fonts.
- **Breaks the math lane.** Revisica's math review depends on `$...$` / `$$...$$` delimited formulas survived through ingestion. Plain text would silently pass a paper with zero extractable math to the math pipeline, producing a meaningless "no issues found" report — worse than a hard failure.
- **Misleading to users.** A successful-looking PDF review that silently skipped all the math is a trust-destroying failure mode. Better to fail loudly at ingestion than succeed emptily at review.
- **Not worth keeping as a toggle.** Even as an opt-in fallback, it creates a "why is my math review empty?" support class we'd rather not have.

## Install Gotcha — Python 3.9 vs MinerU's 3.10+ Requirement

MinerU requires Python `>=3.10,<3.14`. The project's `.venv` is pinned at **3.9.6** for the dual-distribution constraint (documented in the 2026-04-11 learning). So `.venv/bin/pip install mineru` fails with `No matching distribution found for mineru`.

This is **not a real blocker** because [main/index.ts:24-36](../../desktop/src/main/index.ts#L24-L36) already handles it: if the project `.venv` is < 3.10, the desktop app ignores it and uses `python3` on PATH — which on the primary dev machine resolves to pyenv 3.12 with `revisica` already installed editable. MinerU must be installed into **that** Python, not the project `.venv`:

```bash
$(which python3) -m pip install mineru
# or explicitly: ~/.pyenv/shims/python3 -m pip install mineru
```

When we bundle the app for distribution (PyInstaller binary at [main/index.ts:44-48](../../desktop/src/main/index.ts#L44-L48)), MinerU needs to be packaged into that bundle — a separate build-time concern. For now, dev-mode install into pyenv Python is sufficient.

## Install Gotcha — `mineru` vs `mineru[core]`

`pip install mineru` alone installs only the CLI client. The default backend `hybrid-auto-engine` needs local torch/transformers and fails with:

> Error: `hybrid-auto-engine` requires local pipeline dependencies (`mineru[pipeline]`, including `torch`). Install `mineru[pipeline]` or `mineru[core]`.

**Correct install**: `pip install 'mineru[core]'` (pulls torch 2.11, torchvision, transformers 4.57, accelerate, gradio, etc. — ~2 GB of packages).

First parse then downloads ~7 model files from HuggingFace (layout, MFR, OCR-det, VLM) — another ~1 GB on top. Cold first parse: ~3 minutes on Apple Silicon MPS. Subsequent parses: seconds.

End-to-end verified on 2026-04-17 with a trivial test PDF: `parse_document()` returned a `RevisicaDocument` with title, section, and Markdown body containing `$...$` math delimiters.

## Architecture Implications

1. **The silent `ImportError` for Marker is a known latent bug.** We are consciously leaving it in place because fixing it means either implementing Marker or deleting its registry branch — both are scope we've deferred. If someone touches the ingestion registry next, they should decide: implement or remove.

2. **"Install one parser" is now part of the install story.** Until PDF support ships as a default dependency (e.g., bundling MinerU in `pyproject.toml`), anyone who wants PDF must `pip install mineru` manually. The error message at [registry.py:97-103](../../src/revisica/ingestion/registry.py#L97-L103) already tells users this. `revisica bootstrap` does not install it — consider adding a `--with-pdf` flag if user friction shows up.

3. **MinerU is heavy** (~2 GB model download on first run, torch dependency). Bundling it as a default would balloon the wheel size. Keep it optional; document it as required for PDF in the README.

4. **Mathpix remains the cloud escape hatch.** For users who cannot install MinerU (no GPU/MPS, locked-down corporate machine), `MATHPIX_APP_ID` / `MATHPIX_APP_KEY` env vars activate [mathpix_parser.py](../../src/revisica/ingestion/mathpix_parser.py) with no code change. This is opt-in and will never be auto-selected, per the privacy ordering.
