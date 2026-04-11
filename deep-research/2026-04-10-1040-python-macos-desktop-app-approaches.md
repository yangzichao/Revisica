# Python Backend + Web Frontend macOS Desktop App: 2025-2026 State of the Approaches

## Answer

Four main patterns exist for shipping a Python backend with a web frontend as a macOS .app. Electron + Python sidecar is the most production-proven pattern with the richest tooling ecosystem. Tauri 2.0 sidecar has active notarization bugs as of early 2026. pywebview is mature for UI but signing is still manual-heavy. Briefcase (BeeWare) is the only tool that handles packaging + signing + notarization as a single integrated command.

---

## Approach 1: Electron + Python Sidecar

### Bundling Mechanism

The standard pattern uses **python-build-standalone** (maintained by Gregory Szorc, also used by PyOxidizer) to ship a pre-built, self-contained CPython binary. This is placed in the app's `extraResources` via electron-builder, landing at `Datasette.app/Contents/Resources/python`. JavaScript spawns it via Node's `child_process.execFile()`.

Alternatively, Python can be compiled into a single executable via **PyInstaller** (`pyinstaller -F`), and that binary is listed in electron-builder's `files` array. The PyInstaller approach produces a smaller dependency surface but loses the ability to dynamically `pip install` at runtime (which Datasette Desktop uses for plugins).

**electron-builder configuration pattern:**
```json
"extraResources": [
  { "from": "python", "to": "python", "filter": ["**/*"] }
]
```

### Code Signing and Notarization

This is well-solved and documented end-to-end. The workflow:

1. Obtain a **Developer ID Application** certificate ($99/year Apple Developer account).
2. Export as `.p12`, store as GitHub Actions secret (`CSC_LINK` as base64, `CSC_KEY_PASSWORD`).
3. electron-builder handles signing automatically when the certificate is present.
4. **electron-notarize** (now `@electron/notarize`) submits the bundle to Apple's servers; the ticket is stapled to the `.dmg`.
5. Python binaries (including `.so` dynamic libs) must be **explicitly listed** in the signing config — they are not auto-discovered.
6. An `Entitlements.plist` must include `com.apple.security.cs.allow-unsigned-executable-memory` for Python's JIT.

Simon Willison documented the complete GitHub Actions workflow for Datasette Desktop, which bundles Python 3.9.

### Auto-Update

electron-builder ships **electron-updater**, which uses **Squirrel.Mac** on macOS. Updates require a signed app. The standard host is a GitHub Releases endpoint, or a self-hosted update server. The update mechanism applies on next restart.

### App Size

A python-build-standalone CPython 3.9 + minimal packages adds ~50-80 MB to the bundle before stripping. Full Electron runtime adds another ~120-150 MB. Total .app bundles of 200-400 MB are typical.

### Production Examples

- **Datasette Desktop** (Simon Willison, 2021-present) — full Python 3.9 bundled via python-build-standalone, supports runtime `pip install`, ships on GitHub Releases with code signing + notarization via GitHub Actions.
- **JupyterLab Desktop** — Electron app wrapping JupyterLab with a bundled Python environment.

### Maturity Assessment

**High.** The toolchain (electron-builder + python-build-standalone + electron-notarize) is stable and the end-to-end workflow is well-documented with real production apps demonstrating it.

---

## Approach 2: Tauri 2.0 + Python Sidecar

### Bundling Mechanism

Tauri 2.0 uses the `externalBin` array in `tauri.conf.json` to declare sidecar binaries. The binary must be named with a target triple suffix (e.g., `my-server-aarch64-apple-darwin` for Apple Silicon). PyInstaller compiles the Python code into a single executable (`-F` flag), which Tauri then bundles.

```json
"bundle": {
  "externalBin": ["binaries/python-server"]
}
```

A community library **tauri-plugin-python** (on crates.io) exists as an alternative, using RustPython or PyO3 — RustPython removes the need for Python to be installed on the target machine but is not CPython-compatible for complex packages.

### Code Signing and Notarization — ACTIVE BUG

**This is a known, open issue as of March 2026** (GitHub Issue #11992). When any `externalBin` sidecar is present, Apple's notarization service rejects the bundle with "The signature of the binary is invalid." The app builds and notarizes successfully without sidecars.

**Workaround**: manually specify the login keychain during signing:
```shell
codesign -f --timestamp --entitlements entitlements.plist \
  --sign "Developer ID Application" --options runtime \
  --keychain $HOME/Library/Keychains/login.keychain-db BINARY_NAME
```

Without sidecars, Tauri 2.0 signing + notarization works — the `tauri-apps/tauri-action` GitHub Action automates it and the author of the "Stik" note app documented a complete working workflow for a non-sidecar Tauri 2.0 app.

### Auto-Update

Tauri has a first-party **tauri-plugin-updater**. Configure a key pair and update endpoint in `tauri.conf.json`. Updates download in the background and apply on next restart. This is part of Tauri 2.0 and works independently of whether sidecars are used.

### App Size

Tauri apps are dramatically smaller than Electron — the Rust/WebKit core is ~10-20 MB. The PyInstaller Python binary adds 50-100 MB depending on dependencies. Total: ~80-150 MB, roughly 2x smaller than Electron equivalents.

### Process Management Limitation

Because PyInstaller wraps Python in a bootloader process, `process.kill()` on the PID known to Tauri only kills the bootloader, not the Python process. Graceful shutdown must use stdin/stdout messaging rather than SIGTERM.

### Production Examples

No widely known production apps using the Tauri + Python sidecar pattern on macOS were found. The best-documented reference is `dieharders/example-tauri-v2-python-server-sidecar` (115 stars), which is an educational template, not a shipped product.

### Maturity Assessment

**Medium/Low for Python sidecar specifically.** Tauri 2.0 itself is production-ready for pure-Rust backends. The Python sidecar path has an active, unresolved notarization bug and no confirmed production macOS apps. Use with caution until Issue #11992 is resolved.

---

## Approach 3: pywebview + PyInstaller / Briefcase

### pywebview

pywebview (v6.1, BSD, maintained since 2014) wraps the system WebKit component (`WKWebView` on macOS) in a native window. It explicitly describes itself as "bundler friendly" with first-class support for PyInstaller, Nuitka, and py2app. The Python process and the web UI run in the same process — there is no separate HTTP sidecar.

**Advantage**: no cross-process HTTP overhead, smaller architecture.  
**Limitation**: the webview is whatever WKWebKit version ships with macOS — no Chromium pinning, so CSS/JS features depend on the OS version.

### PyInstaller + macOS Signing

PyInstaller is mature but macOS signing is **not automatic** — it is one of the most commonly reported pain points:

- PyInstaller places `base_library.zip` in `Contents/MacOS`, which causes notarization to fail without special handling.
- Code signing must be done **inside-out** (sign each `.so` and `.dylib` individually before signing the outer `.app`) — the `--deep` flag is explicitly discouraged by Apple and PyInstaller maintainers.
- The Hardened Runtime must be enabled, with the `com.apple.security.cs.allow-unsigned-executable-memory` entitlement for Python.
- The `altool` notarization workflow is deprecated; `notarytool` is the current standard.

Multiple open issues on the PyInstaller GitHub tracker (including #5112, #7937) document ongoing signing edge cases, particularly with frameworks like Qt WebEngine. Pure pywebview apps (using system WebKit) avoid the Qt issues.

### Briefcase (BeeWare)

Briefcase (current: v0.3.25, with v0.3.26 in dev) is the most **integrated** signing solution for Python apps. Key facts:

- `briefcase package macOS` automatically signs AND notarizes the app in a single command, prompting for the certificate to use.
- Output formats: `.app` bundle, `.dmg`, `.pkg`, or zipped `.app`.
- Apps are signed with a Developer ID Application certificate; notarization is submitted to Apple automatically unless an ad-hoc identity is used.
- **2025 feature**: Briefcase was modified to package, sign, and notarize apps built with *other* tools — not just Briefcase-native apps.
- No built-in auto-update mechanism.

### Auto-Update

Neither pywebview nor Briefcase provide auto-update out of the box. The typical approach is to ship a Sparkle-based updater or implement a manual update-check in Python.

### App Size

System WebKit means no bundled browser engine. A typical pywebview app + PyInstaller is 40-100 MB depending on Python dependencies — the smallest footprint of the four approaches.

### Production Examples

pywebview's homepage lists several commercial apps, but specific macOS production examples with full signing pipelines are not well-documented publicly. It is widely used for internal tooling.

### Maturity Assessment

**Medium.** pywebview itself is stable and mature. The signing story with PyInstaller is workable but requires manual effort and has known rough edges. Briefcase makes signing easier but adds its own abstraction layer. No auto-update story out of the box.

---

## Approach 4: Other Approaches Worth Knowing

### flaskwebgui

`flaskwebgui` (GitHub: ClimenteA/flaskwebgui) wraps a Flask/Django/FastAPI server in a Chrome/Edge window, using PyInstaller or pyvan for bundling. It is not macOS-native (requires Chrome/Edge installed or bundled) and has no integrated signing support. Suitable for internal tools, not for App Store or notarized distribution.

### Reflex

Reflex compiles Python to a React frontend + FastAPI backend. It is a full-stack framework, not a desktop app packager. No native .app distribution support.

### py2app

py2app (macOS-only) produces `.app` bundles from Python scripts without PyInstaller. It is older, less actively maintained, and has a smaller community than PyInstaller, but Briefcase uses it under the hood for some macOS targets.

---

## Comparative Summary Table

| Criterion | Electron + Python sidecar | Tauri 2.0 + Python sidecar | pywebview + PyInstaller | Briefcase (BeeWare) |
|---|---|---|---|---|
| **Signing** | Well-solved via electron-builder | Works without sidecar; sidecar has active bug | Manual, works with care | Automated (`briefcase package`) |
| **Notarization** | Automated via electron-notarize | Broken with sidecar (Issue #11992, open Mar 2026) | Manual, known edge cases | Automated |
| **Auto-update** | Built-in (electron-updater / Squirrel) | Built-in (tauri-plugin-updater) | None out of box | None out of box |
| **App size** | ~200-400 MB | ~80-150 MB | ~40-100 MB | ~40-100 MB |
| **Production macOS examples** | Datasette Desktop, JupyterLab Desktop | None confirmed | Some commercial apps | Limited public examples |
| **Python bundling maturity** | High (python-build-standalone) | Low (PyInstaller sidecar + bug) | Medium (PyInstaller quirks) | Medium (integrated tooling) |
| **Webview engine** | Chromium (pinned) | System WebKit | System WebKit | System WebKit |

---

## Confidence & Caveats

**High confidence** on Electron: the Datasette Desktop project is a real, public, maintained app with fully documented CI/CD for macOS signing/notarization.

**High confidence** on the Tauri sidecar notarization bug: documented in an open GitHub issue last updated March 2026 with confirmed reproduction.

**Medium confidence** on pywebview/Briefcase production usage: the signing workflows are documented, but large-scale production app examples are not publicly prominent.

The Tauri notarization bug is the most significant risk differentiator — if it gets resolved, Tauri 2.0 becomes a compelling choice due to smaller bundle size and built-in updater.

---

## Sources

- [Bundling Python inside an Electron app (Simon Willison TIL)](https://til.simonwillison.net/electron/python-inside-electron)
- [Signing and notarizing an Electron app for distribution using GitHub Actions (Simon Willison TIL)](https://til.simonwillison.net/electron/sign-notarize-electron-macos)
- [Datasette Desktop announcement](https://simonwillison.net/2021/Sep/8/datasette-desktop/)
- [Tauri 2.0 Sidecar Documentation](https://v2.tauri.app/develop/sidecar/)
- [Tauri macOS Code Signing Documentation](https://v2.tauri.app/distribute/sign/macos/)
- [Tauri Issue #11992: MacOS Codesigning and notarization issue when using ExternalBin](https://github.com/tauri-apps/tauri/issues/11992)
- [example-tauri-v2-python-server-sidecar (dieharders)](https://github.com/dieharders/example-tauri-v2-python-server-sidecar)
- [Shipping a Production macOS App with Tauri 2.0: Code Signing, Notarization, and Homebrew](https://dev.to/0xmassi/shipping-a-production-macos-app-with-tauri-20-code-signing-notarization-and-homebrew-mc3)
- [tauri-plugin-python on crates.io](https://crates.io/crates/tauri-plugin-python)
- [pywebview official site](https://pywebview.flowrl.com/)
- [Briefcase macOS documentation (stable)](https://briefcase.beeware.org/en/stable/reference/platforms/macOS/)
- [Briefcase macOS code signing how-to](https://briefcase.beeware.org/en/stable/how-to/code-signing/macOS/)
- [Building Production-Ready Desktop LLM Apps: Tauri, FastAPI, and PyInstaller](https://aiechoes.substack.com/p/building-production-ready-desktop)
- [electron-notarize GitHub](https://github.com/electron/notarize)
- [electron-builder auto-update](https://www.electron.build/auto-update.html)
- [PyInstaller code signing issue #5112](https://github.com/pyinstaller/pyinstaller/issues/5112)
- [flaskwebgui GitHub](https://github.com/ClimenteA/flaskwebgui)
