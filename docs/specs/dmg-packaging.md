# Spec: DMG Packaging — Bundling Python Backend + External Tools

**Status:** draft
**First drafted:** 2026-04-12
**Last revised:** 2026-04-17 (pyproject alignment, hidden-import widening, smoke-test criteria)

## Problem

Revisica desktop is an Electron app with a Python (FastAPI) sidecar. For end users to run it without installing Python, pip, or CLI tools, the DMG must ship a self-contained bundle that includes:

1. The frozen Python backend (currently runs from source via `python -m revisica.api`)
2. Pandoc binary (required for `.tex` parsing — the only high-quality LaTeX→Markdown path)

Without bundling, users must install Python 3.10+, `pip install revisica`, and `brew install pandoc` themselves. That defeats the purpose of a desktop app.

## Current State

**What exists:**
- `desktop/electron-builder.yml` — configured for DMG, `extraResources` pointing to empty `resources/` dir
- `desktop/src/main/index.ts` — dev mode: spawns `python3 -m revisica.api`; production mode: expects `resources/python-backend/python-backend` binary (not yet built)
- `pyproject.toml` — declares `requires-python = ">=3.10"` and `langgraph>=0.5` as a core runtime dependency (the graphs subpackage is imported unconditionally by every review path).
- No `desktop/build/entitlements.mac.plist`, no PyInstaller spec, no CI pipeline.

**What's missing:**
- PyInstaller build for the Python backend
- Pandoc binary in app resources
- Code signing + notarization
- CI/CD pipeline
- A working dev-mode fallback for the silent "system python3 is 3.9" trap on fresh macOS installs (`main/index.ts:27-33` currently prefers venv Python if ≥3.10, otherwise drops to plain `python3` — which is often 3.9 on macOS and fails at graph compile with `TypeError: unsupported operand type(s) for |`).

## Design

**Target:** arm64 only (Apple Silicon). Intel Mac not supported.

### Bundle layout inside `Revisica.app`

```
Revisica.app/Contents/
├── MacOS/
│   └── Revisica                          # Electron main process
├── Resources/
│   ├── app.asar                          # Electron renderer (React)
│   └── resources/
│       ├── python-backend/               # PyInstaller --onedir output (~80-120 MB)
│       │   ├── python-backend            # Main executable
│       │   └── ...                       # Shared libs, data files
│       ├── LICENSES/
│       │   └── pandoc-GPL2.txt           # Pandoc license (required by GPL-2)
│       └── ...
└── Frameworks/
    └── Electron Framework.framework/
```

Pandoc is embedded inside the Python bundle via `pypandoc-binary` — no separate binary to manage.

### Component strategy

| Component | Size | Bundle? | How |
|-----------|------|---------|-----|
| Python backend | ~80-120 MB | Yes, required | PyInstaller `--onedir` |
| Pandoc | ~25 MB | Yes, required | `pypandoc-binary` pip package, bundled inside PyInstaller output automatically |
| Marker | ~50 MB code + ~200 MB models | No | User installs separately if they want local PDF |
| MinerU | ~2+ GB (PyTorch) | No | User installs separately; detected via `shutil.which("mineru")` |
| Mathpix | 0 | No | Cloud API, user provides key in Settings |

**Total DMG size estimate:** ~150-180 MB

### Step 1: PyInstaller Python Backend

Freeze `revisica.api:main` using `--onedir` mode (faster startup than `--onefile`).

```bash
# From project root — build with a dedicated venv, NOT the dev venv, so
# stray local packages don't leak into the bundle.
/opt/homebrew/bin/python3.12 -m venv .build-venv        # 3.12 has the most
                                                         # mature wheel matrix
                                                         # across langchain/
                                                         # pydantic-core/orjson.
                                                         # 3.13 works but some
                                                         # wheels still ship
                                                         # late.
source .build-venv/bin/activate
pip install -e ".[all]"          # sympy + langgraph (base) + fastapi/uvicorn
                                 # (serve) + anthropic/openai (api)
pip install pypandoc-binary      # embeds pandoc — PyInstaller picks it up
pip install pyinstaller

pyinstaller \
  --name python-backend \
  --onedir \
  # revisica's own dynamic-ish imports (registries use static `from` so
  # PyInstaller's analyzer traces them, but listing the leaves makes the
  # build robust against future refactors and surface registry failures
  # loudly at build time rather than silently at runtime).
  --hidden-import revisica.ingestion.markdown_parser \
  --hidden-import revisica.ingestion.tex_parser \
  --hidden-import revisica.ingestion.pandoc_parser \
  --hidden-import revisica.ingestion.mineru_parser \
  --hidden-import revisica.ingestion.mathpix_parser \
  --hidden-import revisica.ingestion.marker_parser \
  # uvicorn protocol auto-detection
  --hidden-import uvicorn.logging \
  --hidden-import uvicorn.loops.auto \
  --hidden-import uvicorn.protocols.http.auto \
  --hidden-import uvicorn.lifespan.on \
  # langchain/langgraph ecosystem uses lazy-loaded plugins + `if TYPE_CHECKING`
  # imports that PyInstaller's static analyzer doesn't always trace; pull the
  # whole trees to be safe. Inflates bundle by ~30-40 MB but avoids whack-a-
  # mole ModuleNotFoundError at runtime.
  --collect-submodules langgraph \
  --collect-submodules langgraph_checkpoint \
  --collect-submodules langgraph_prebuilt \
  --collect-submodules langchain_core \
  --collect-submodules langsmith \
  --collect-submodules pydantic \
  --collect-submodules pydantic_core \
  # data files
  --collect-data revisica \
  --collect-data pypandoc_binary \
  --collect-data langchain_core \
  src/revisica/api.py
```

Output: `dist/python-backend/` directory → copy to `desktop/resources/python-backend/`.

Why `--onedir`: The Python backend is a sidecar process spawned at app startup. `--onedir` avoids the extraction-to-temp-dir step that `--onefile` requires, so the backend starts in ~1s instead of ~5s. The directory is hidden inside the `.app` bundle anyway.

Why Python 3.12 for the build venv: the langchain/langgraph/pydantic-core stack ships arm64 wheels for 3.11 and 3.12 on first-day releases; 3.13/3.14 wheels sometimes lag a few weeks. The dev venv can run 3.13 without penalty (verified in this session), but shipped bundles want the most conservative interpreter with wheel-complete deps. Revisit once 3.13 wheels are universal.

### Step 2: Pandoc Discovery in Production

`pypandoc-binary` embeds the pandoc binary inside the Python package. PyInstaller bundles it automatically via `--collect-data pypandoc_binary`.

Update `pandoc_parser.py` to add a fallback when `shutil.which("pandoc")` fails:

```python
@classmethod
def is_available(cls) -> bool:
    if shutil.which("pandoc"):
        return True
    # Fallback: check pypandoc-binary (bundled in PyInstaller)
    try:
        import pypandoc
        return bool(pypandoc.get_pandoc_path())
    except (ImportError, OSError):
        return False
```

No env vars, no `electron-builder.yml` changes, no separate binary to manage.

### Step 3: Electron Main Process Updates

`desktop/src/main/index.ts` already handles dev vs production. The only change: production path points to the `--onedir` output.

```typescript
// Production: use bundled PyInstaller directory
const resourcePath = join(process.resourcesPath, 'resources', 'python-backend', 'python-backend')
return {
  command: resourcePath,
  args: ['--port', String(API_PORT)]
}
```

No env vars needed — `pypandoc-binary` is inside the PyInstaller bundle.

### Step 4: Code Signing + Notarization

All binaries inside the `.app` bundle must be signed. With `--onedir`, there are multiple binaries and shared libs inside `python-backend/`:

```bash
# Sign all binaries inside PyInstaller output (inside-out)
find "Revisica.app/Contents/Resources/resources/python-backend" \
  -type f \( -name "*.dylib" -o -name "*.so" -o -perm +111 \) \
  -exec codesign --force --options runtime --sign "$DEVELOPER_ID" {} \;

# Sign the app itself
codesign --force --deep --options runtime --sign "$DEVELOPER_ID" \
  --entitlements build/entitlements.mac.plist \
  "Revisica.app"

# Notarize
xcrun notarytool submit Revisica.dmg --apple-id "$APPLE_ID" --team-id "$TEAM_ID" --wait
```

**Entitlements needed:**
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "...">
<plist version="1.0">
<dict>
  <key>com.apple.security.cs.allow-jit</key>           <true/>
  <key>com.apple.security.cs.allow-unsigned-executable-memory</key> <true/>
  <key>com.apple.security.cs.allow-dyld-environment-variables</key> <true/>
  <key>com.apple.security.files.user-selected.read-write</key>     <true/>
  <key>com.apple.security.network.client</key>         <true/>
</dict>
</plist>
```

### Step 5: CI/CD (GitHub Actions)

```yaml
# .github/workflows/build-dmg.yml
jobs:
  build:
    runs-on: macos-14  # Apple Silicon runner
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.12' }
      - run: pip install ".[all]" pypandoc-binary pyinstaller   # [all] = [api,serve]; langgraph is a base dep
      - run: bash scripts/build-python-backend.sh
      - run: cd desktop && npm ci && npm run build:mac
      - run: # sign + notarize
      - uses: actions/upload-artifact@v4
        with: { name: "Revisica-arm64.dmg", path: "desktop/dist/*.dmg" }
```

### PDF Parsers: Not Bundled

PDF parsing tools (MinerU, Marker, Mathpix) are not bundled in the DMG. Users who need PDF support can:

1. **Mathpix** — Set API key in Settings page (cloud, ~$0.01/page)
2. **MinerU** — `pip install mineru` (local, needs GPU)
3. **Marker** — `pip install marker-pdf` (local, no GPU)

The app detects these at runtime via `shutil.which()` and env vars. The Settings/Help page should document installation options.

## Licensing

| Component | License | Bundling implication |
|-----------|---------|---------------------|
| Pandoc | GPL-2.0-or-later | OK — invoked as subprocess (mere aggregation). Must include GPL text + source link. |
| Python | PSF-2.0 | Permissive, no issue. |
| PyInstaller | GPL-2.0 (bootloader exception) | Bundled apps are explicitly allowed. |
| Revisica | MIT | No conflict with any of the above. |

**Required in bundle:** `Resources/LICENSES/` directory with `pandoc-GPL2.txt`. About dialog links to Pandoc source repo.

## Implementation Plan

Order matters — later steps depend on earlier ones. Do not start step N+1 without the acceptance evidence for step N.

1. [ ] Create `desktop/build/entitlements.mac.plist` with the entitlements listed above.
2. [ ] Add `pypandoc-binary` to `[project.optional-dependencies]` as a `bundle` extra so `pip install .[bundle]` pulls it during build without polluting regular dev installs.
3. [ ] Update `src/revisica/ingestion/pandoc_parser.py` — fall back to `pypandoc.get_pandoc_path()` when `shutil.which("pandoc")` returns nothing; add a unit test.
4. [ ] Write `scripts/build-python-backend.sh` (and a matching `python-backend.spec` if the inline-flags version becomes unwieldy) — fresh build-venv with Python 3.12, installs `.[all,bundle] pyinstaller`, runs PyInstaller, copies `dist/python-backend/` to `desktop/resources/python-backend/`. Script must be idempotent and leave no stale files.
5. [ ] **Smoke test the frozen binary before touching Electron.** Run `desktop/resources/python-backend/python-backend --port 18999` in a fresh terminal (no venv, no PYTHONPATH), then `curl http://127.0.0.1:18999/api/health` should return `{"status":"ok"}`, `curl -X POST /api/ingest` on a sample `.tex` and `.md` must succeed, `/api/review` must kick off without `ModuleNotFoundError`. If anything fails here, widen `--collect-submodules`, do NOT ship.
6. [ ] Update `desktop/src/main/index.ts` — production branch's path changes from `resources/python-backend` (a file) to `resources/python-backend/python-backend` (exec inside a folder).
7. [ ] Update `desktop/electron-builder.yml` — already arm64-only; double-check `extraResources` still mirrors `desktop/resources/`; add any codesign/entitlement stanzas electron-builder needs to pick up the inner binaries.
8. [ ] Add `desktop/resources/LICENSES/pandoc-GPL2.txt` verbatim from the upstream Pandoc LICENSE file. About dialog gets a link to the Pandoc source repo.
9. [ ] Full build: `npm run build:mac` produces a DMG that installs, launches, and passes the full acceptance-criteria list on a clean Mac.
10. [ ] Add codesign + `xcrun notarytool submit --wait` steps to the build script (gated on `APPLE_ID`, `TEAM_ID`, `DEVELOPER_ID` env vars).
11. [ ] Create `.github/workflows/build-dmg.yml` using `macos-14` (arm64) runners.

## Acceptance Criteria

All of these must be green before the spec flips to `done`.

- [ ] `npm run build:mac` produces `Revisica-0.1.0-arm64.dmg`.
- [ ] DMG installs and launches on a Mac with **no Python, no Homebrew, no pip**.
- [ ] **Frozen-binary smoke test (runs standalone, not via Electron):**
  - [ ] `python-backend --port 18999 &` + `curl http://127.0.0.1:18999/api/health` returns 200 within 5 s of launch.
  - [ ] `curl -X POST /api/ingest` on a `.tex` fixture returns valid JSON with `parser_used: "pandoc"`.
  - [ ] `curl -X POST /api/ingest` on a `.md` fixture returns valid JSON with `parser_used: "markdown"`.
  - [ ] `curl -X POST /api/review` on a fixture returns a `run_id` and the `/api/status/{run_id}` reaches `completed` or `failed` (not crashes with `ModuleNotFoundError`).
- [ ] App launches to first-interactive within ~3 s of DMG double-click (measured manually).
- [ ] DMG size < 200 MB.
- [ ] `Revisica.app/Contents/Resources/resources/LICENSES/pandoc-GPL2.txt` present.
- [ ] Notarized: `spctl --assess --type execute Revisica.app` prints `accepted`.

## References

- Decision source: this spec currently carries the PyInstaller `--onedir` choice inline; extract to a dedicated ADR (`docs/decisions/NNNN-pyinstaller-onedir.md`) before marking `approved` so the rationale is preserved if the bundling approach is ever reconsidered (Nuitka, Briefcase, UV-bundled Python, Tauri migration).
- Parent: [Desktop app architecture](desktop-app.md).
- Learning (to be written post-ship): measure the actual DMG size, startup time, and hidden-import holes that only appear in the frozen build — log in `docs/learning/YYYY-MM-DD-dmg-first-ship.md`.
