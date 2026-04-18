# Learning: MinerU Install Gotchas and First-Run Timing

**Date:** 2026-04-17
**Commit:** `fc72602`
**Validates:** [docs/decisions/0001-pdf-parser-mineru.md](../decisions/0001-pdf-parser-mineru.md)

**Context:** After accepting [ADR 0001](../decisions/0001-pdf-parser-mineru.md) (MinerU as default PDF parser), the first hands-on install surfaced two non-obvious gotchas and a first-parse cost worth recording for anyone repeating this setup.

## Gotcha 1 — Python 3.9 vs MinerU's 3.10+ requirement

MinerU requires Python `>=3.10,<3.14`. The project's `.venv` is pinned at **3.9.6** for dual-distribution reasons (see [docs/learning/2026-04-11-dual-distribution-provider-mode.md](2026-04-11-dual-distribution-provider-mode.md)). So `.venv/bin/pip install mineru` fails with `No matching distribution found for mineru`.

This is **not a real blocker** because [main/index.ts:24-36](../../desktop/src/main/index.ts#L24-L36) already handles it: if the project `.venv` is < 3.10, the desktop app ignores it and uses `python3` on PATH — which on the primary dev machine resolves to pyenv 3.12 with `revisica` already installed editable. MinerU must be installed into **that** Python, not the project `.venv`:

```bash
$(which python3) -m pip install mineru
# or explicitly: ~/.pyenv/shims/python3 -m pip install mineru
```

When we bundle the app for distribution (PyInstaller binary at [main/index.ts:44-48](../../desktop/src/main/index.ts#L44-L48)), MinerU needs to be packaged into that bundle — a separate build-time concern. For now, dev-mode install into pyenv Python is sufficient.

## Gotcha 2 — `mineru` vs `mineru[core]`

`pip install mineru` alone installs only the CLI client. The default backend `hybrid-auto-engine` needs local torch/transformers and fails with:

> Error: `hybrid-auto-engine` requires local pipeline dependencies (`mineru[pipeline]`, including `torch`). Install `mineru[pipeline]` or `mineru[core]`.

**Correct install:** `pip install 'mineru[core]'` (pulls torch 2.11, torchvision, transformers 4.57, accelerate, gradio — ~2 GB of packages).

## First-run cost

First parse downloads ~7 model files from HuggingFace (layout, MFR, OCR-det, VLM) — another ~1 GB on top of the ~2 GB of Python deps. Cold first parse: ~3 minutes on Apple Silicon MPS. Subsequent parses: seconds.

End-to-end verified 2026-04-17 with a trivial test PDF: `parse_document()` returned a `RevisicaDocument` with title, section, and Markdown body containing `$...$` math delimiters.

## Lesson

Install-time constraints for local ML parsers are meaningfully larger than they appear in the CLI help: a `pip install mineru` command hides ~3 GB of download and ~3 minutes of first-run cost. When shipping MinerU to end users (either via `revisica bootstrap --with-pdf` or a bundled desktop binary), the installer should surface this up front rather than surprise the user during their first drag-and-drop.

## Architecture implications

1. **Two Pythons is now a fact, not a bug.** The `.venv` is for Python 3.9 dual-distribution work; MinerU lives in pyenv 3.12 (or the distribution-bundled Python). Any script that assumes a single Python environment is wrong. The desktop app's detection logic at [main/index.ts:24-36](../../desktop/src/main/index.ts#L24-L36) is load-bearing.

2. **`revisica bootstrap` should grow a `--with-pdf` flag** once this gotcha shows up in real user friction. Until then, the error message at [registry.py:97-103](../../src/revisica/ingestion/registry.py#L97-L103) is sufficient.

3. **Bundling MinerU into a default wheel is a non-starter.** ~3 GB of dependencies and model downloads make it clearly optional. Keep the registry's silent-on-missing-parser behavior, but keep the error message loud when a PDF is dragged and no parser is available.
