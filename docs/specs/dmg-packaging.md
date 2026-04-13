# Spec: DMG Packaging — Bundling Python Backend + External Tools

**Status:** draft (Pandoc installed locally, benchmark validated)
**Date:** 2026-04-12

## Problem

Revisica desktop is an Electron app with a Python (FastAPI) sidecar. For end users to run it without installing Python, pip, or CLI tools, the DMG must ship a self-contained bundle that includes:

1. The frozen Python backend (currently runs from source via `python -m revisica.api`)
2. Pandoc binary (required for `.tex` parsing — the only high-quality LaTeX→Markdown path)

Without bundling, users must install Python 3.10+, `pip install revisica`, and `brew install pandoc` themselves. That defeats the purpose of a desktop app.

## Current State

**What exists:**
- `desktop/electron-builder.yml` — configured for DMG, `extraResources` pointing to empty `resources/` dir
- `desktop/src/main/index.ts` — dev mode: spawns `python3 -m revisica.api`; production mode: expects `resources/python-backend` binary (not yet built)
- `build/entitlements.mac.plist` — referenced but does not exist yet
- No PyInstaller spec, no CI pipeline

**What's missing:**
- PyInstaller build for the Python backend
- Pandoc binary in app resources
- Code signing + notarization
- CI/CD pipeline

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
# From project root, with venv activated
pip install pyinstaller
pip install "revisica[serve]"      # fastapi + uvicorn
pip install pypandoc-binary        # embeds pandoc binary — PyInstaller picks it up

pyinstaller \
  --name python-backend \
  --onedir \
  --hidden-import revisica.ingestion.markdown_parser \
  --hidden-import revisica.ingestion.tex_parser \
  --hidden-import revisica.ingestion.pandoc_parser \
  --hidden-import revisica.ingestion.mineru_parser \
  --hidden-import revisica.ingestion.mathpix_parser \
  --hidden-import revisica.ingestion.marker_parser \
  --hidden-import uvicorn.logging \
  --hidden-import uvicorn.loops.auto \
  --hidden-import uvicorn.protocols.http.auto \
  --hidden-import uvicorn.lifespan.on \
  --collect-data revisica \
  --collect-data pypandoc_binary \
  src/revisica/api.py
```

Output: `dist/python-backend/` directory → copy to `desktop/resources/python-backend/`.

Why `--onedir`: The Python backend is a sidecar process spawned at app startup. `--onedir` avoids the extraction-to-temp-dir step that `--onefile` requires, so the backend starts in ~1s instead of ~5s. The directory is hidden inside the `.app` bundle anyway.

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
      - run: pip install ".[all,serve]" pypandoc-binary pyinstaller
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

1. [ ] Create `desktop/build/entitlements.mac.plist`
2. [ ] Add `pypandoc-binary` to `[project.optional-dependencies]` as `bundle` extra
3. [ ] Update `pandoc_parser.py` — fallback to `pypandoc.get_pandoc_path()` when `shutil.which` fails
4. [ ] Write `scripts/build-python-backend.sh` — PyInstaller `--onedir` + copy to `desktop/resources/`
5. [ ] Update `desktop/src/main/index.ts` — production path to `python-backend/python-backend`
6. [ ] Update `desktop/electron-builder.yml` — arm64 only, remove x64
7. [ ] Add `desktop/resources/LICENSES/pandoc-GPL2.txt`
8. [ ] Test: `npm run build:mac` produces working DMG on arm64
9. [ ] Add code signing + notarization to build script
10. [ ] Create `.github/workflows/build-dmg.yml`

## Acceptance Criteria

- [ ] `npm run build:mac` produces `Revisica-0.1.0-arm64.dmg`
- [ ] DMG installs and launches on a clean Mac (no Python, no Homebrew)
- [ ] App can parse `.tex` files (Pandoc works via `pypandoc-binary` in bundle)
- [ ] App can parse `.md`/`.mmd` files (built-in markdown parser)
- [ ] `/api/health` responds within 5 seconds of launch (`--onedir` fast startup)
- [ ] `/api/ingest` with a `.tex` file returns valid RevisicaDocument
- [ ] DMG size < 200 MB
- [ ] `LICENSES/pandoc-GPL2.txt` present in bundle
- [ ] Notarized: passes `spctl --assess --type execute`
