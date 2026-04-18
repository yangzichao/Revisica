# 0002. Freeze the Python backend with PyInstaller `--onedir`

**Status:** Accepted
**Date:** 2026-04-17
**Commit:** `4811ab4`

## Context

Revisica desktop is an Electron app that spawns a FastAPI sidecar written in Python. For end users to run the DMG without installing Python, pip, or `pandoc`, the backend has to ship as a self-contained bundle. The candidates evaluated were:

- **PyInstaller `--onedir`** — freezes the interpreter + all `.pyc` + shared libs into a directory; PyInstaller writes a bootstrapper that `exec`s straight into the app code.
- **PyInstaller `--onefile`** — same, but glued into one executable that extracts to `$TMPDIR` at every launch.
- **Nuitka** — ahead-of-time compiles Python to C; produces faster-starting binaries but has a much longer build (~20 min) and a weaker ecosystem around scientific wheels.
- **Briefcase / BeeWare** — nice UX layer but thin wrapper over PyInstaller/py2app; buys us nothing vs. calling PyInstaller directly.
- **UV-bundled Python** — ship `uv python install` output plus the project source. Compact and fast to build, but the installer is ~40 MB of extra tooling the user never uses, and resolving third-party binaries (pandoc) is still on us.
- **Tauri rewrite** — ruled out as a rewrite, not a bundling change.

The backend already has a clean `python -m revisica.api` entrypoint and imports `langgraph` / `langchain_core` / `pydantic_core` unconditionally from the review path. Startup latency matters: the Electron main process blocks on `/api/health` (up to 30 s) before showing the window ([desktop/src/main/index.ts:87-103](../../desktop/src/main/index.ts#L87-L103)), so anything that adds multi-second boot time is a visible regression.

## Decision

**We will freeze the backend with PyInstaller in `--onedir` mode.**

- Build interpreter pinned to **Python 3.12** (`langchain`/`pydantic-core` ship first-day arm64 wheels for 3.11/3.12; 3.13 wheels lag by weeks).
- The PyInstaller spec lives at [scripts/pyinstaller/python-backend.spec](../../scripts/pyinstaller/python-backend.spec); the orchestration script is [scripts/build-python-backend.sh](../../scripts/build-python-backend.sh).
- Pandoc is embedded via the `pypandoc-binary` wheel under an optional `bundle` extra in [pyproject.toml](../../pyproject.toml) — no separate binary to version or resign.
- The `--onedir` output is copied into `desktop/resources/python-backend/` and picked up by electron-builder via the existing `extraResources` entry.

## Consequences

**Easier:**

- Startup: `--onedir` skips the `$TMPDIR` self-extract step that `--onefile` needs, so the sidecar reaches `/api/health` in ~1 s instead of ~5 s. The directory is invisible inside the `.app` bundle.
- Rebuilds: `scripts/build-python-backend.sh` clears both `scripts/pyinstaller/build/` and `scripts/pyinstaller/dist/` on every run — idempotency wins over incremental speed, since the PyInstaller cache is a common source of "works locally, fails on CI" bugs. Expect ~3 min locally after the first run (venv cached via `REVISICA_KEEP_BUILD_VENV=1`), ~6 min on the `macos-14` GitHub runner from cold.
- Debuggability: when a hidden import is missing, the traceback is a normal Python traceback from the bootstrap script, not a stripped stack from an AOT-compiled binary.
- Signing: with `--onedir` we sign individual dylibs inside-out before signing the outer app, which is the standard Apple pattern. `--onefile` would require signing a runtime-extracted tree that Gatekeeper re-examines per launch.

**Harder / newly risky:**

- Bundle size inflates to ~150–180 MB because `langgraph` / `langchain_core` / `pydantic_core` pull large submodule trees that PyInstaller's static analyzer can't prune safely. Accepted as the cost of avoiding whack-a-mole `ModuleNotFoundError` from lazy-loaded plugins.
- Any new top-level dependency that uses `if TYPE_CHECKING` imports or lazy plugin loading needs a corresponding `collect_submodules(...)` entry in the spec file. Mitigated by running [scripts/smoke-test-python-backend.sh](../../scripts/smoke-test-python-backend.sh) against the frozen binary before Electron gets involved — the smoke test greps the backend log for `ModuleNotFoundError` and fails the build if it finds any.
- Python interpreter is locked at build time. Upgrading from 3.12 to 3.13 is a deliberate CI change, not a silent pickup of whatever is on the runner.
- PDF parsers (MinerU, Marker) are excluded from the bundle on purpose — they would add ~2 GB of PyTorch and GPU runtime. Users install them separately per ADR 0001; the `bundle` build excludes them in [python-backend.spec](../../scripts/pyinstaller/python-backend.spec) so they don't sneak in from a developer's `.build-venv`.

## Revisit trigger

- DMG size exceeds ~300 MB or startup latency exceeds ~3 s in user reports — re-evaluate Nuitka or UV-bundled Python.
- The langchain ecosystem ships a first-party bundling story that PyInstaller can delegate to.
- Cross-platform distribution (Windows/Linux desktops) is prioritized — at that point, Tauri + a smaller Python runtime may be cheaper than maintaining three PyInstaller configs.

## References

- Spec: [docs/specs/dmg-packaging.md](../specs/dmg-packaging.md)
- Build script: [scripts/build-python-backend.sh](../../scripts/build-python-backend.sh)
- PyInstaller spec: [scripts/pyinstaller/python-backend.spec](../../scripts/pyinstaller/python-backend.spec)
- Smoke test: [scripts/smoke-test-python-backend.sh](../../scripts/smoke-test-python-backend.sh)
- Parser policy that keeps PDF tools out of the bundle: [0001-pdf-parser-mineru.md](0001-pdf-parser-mineru.md)
