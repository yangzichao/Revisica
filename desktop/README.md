# Revisica Desktop

Electron + React + Vite shell that wraps the Revisica Python backend (`revisica.api`) and exposes it as a native macOS app.

## Quick commands

> ### ⭐️ Daily driver: `npm run dev`
>
> Starts Electron with HMR **and** auto-spawns the Python backend on port 18321.
> This is the only command you need 95% of the time.

```bash
# 👉 Run the app (HMR + Python backend) — START HERE
npm run dev

# One-off type check on the renderer
npx tsc -p tsconfig.web.json --noEmit

# Build unpacked .app for local testing (no code signing)
CSC_IDENTITY_AUTO_DISCOVERY=false npm run build:unpack
open dist/mac-arm64/Revisica.app

# Health-check the backend while dev is running
curl -s http://127.0.0.1:18321/api/health

# Find and kill a leaked backend on port 18321
lsof -ti :18321 | xargs kill

# Nuke and reinstall node_modules if things get weird
rm -rf node_modules && npm install

# Tail backend logs from a backgrounded `npm run dev`
# (logs are prefixed with [python] in the same terminal)
```

## Architecture

```
Electron main (src/main/index.ts)
  ├─ spawns Python backend (uvicorn on 127.0.0.1:18321)
  │     dev:   python3 -m revisica.api --port 18321
  │     prod:  resources/python-backend  (PyInstaller binary)
  ├─ mints a per-launch API token, passes it to backend via REVISICA_API_TOKEN
  └─ creates BrowserWindow, sends { apiBase, apiToken } to renderer via IPC

Renderer (src/renderer/) — React app, calls the backend with apiFetch()
```

The token is regenerated every launch and never leaves the machine — it just prevents drive-by requests from other local processes hitting the API.

## Prerequisites

1. Python venv with revisica installed at the repo root:
   ```bash
   cd ..
   python3 -m venv .venv && . .venv/bin/activate
   python -m pip install .
   ```
   Dev mode looks for `.venv/bin/python3` (Python 3.10+) and falls back to system `python3`.

2. Node deps:
   ```bash
   npm install
   ```

## Development

```bash
npm run dev
```

Starts electron-vite with HMR. The main process spawns the Python backend on port 18321 and waits up to 30s for `/api/health` to return 200 before opening the window.

**Closing the window quits the entire dev session** (Electron + Python). To stop cleanly, just close the window or `Ctrl+C` the terminal.

Backend logs are prefixed with `[python]` in the dev terminal. Renderer DevTools open with `Cmd+Opt+I`.

## Packaging

```bash
# Unpacked .app for local testing (no signing)
CSC_IDENTITY_AUTO_DISCOVERY=false npm run build:unpack
open dist/mac-arm64/Revisica.app

# Signed DMG (requires a Developer ID cert + build/entitlements.mac.plist)
npm run build:mac
```

**Important:** packaged builds expect a PyInstaller-frozen Python backend at `resources/python-backend`. Until that exists, the packaged app will boot but show "backend not running" in the UI — use `npm run dev` for end-to-end testing.

To produce the backend binary (one-time setup, not yet wired into CI):
```bash
cd ..
. .venv/bin/activate
pip install pyinstaller
pyinstaller --onefile --name python-backend \
  --distpath desktop/resources \
  -m revisica.api
```

## Common issues

| Symptom | Cause | Fix |
|---|---|---|
| UI shows "Lost connection to backend" | Python process died or crashed during a request | Check `[python]` logs for traceback; restart `npm run dev` |
| "Python backend failed to start within 30 seconds" | venv missing or `revisica.api` not importable | `pip install .` from repo root |
| Packaged app opens but no API | `resources/python-backend` not bundled | Use `npm run dev`, or build the PyInstaller binary above |
| `codesign ... cannot read entitlement data` during build | `build/entitlements.mac.plist` missing | Set `CSC_IDENTITY_AUTO_DISCOVERY=false` for local builds |
| Port 18321 already in use | Previous backend leaked | `lsof -i :18321` then kill the PID |

## Layout

```
desktop/
├── src/
│   ├── main/index.ts        # Electron main: spawns Python, creates window
│   ├── preload/index.ts     # IPC bridge (api-config event)
│   ├── renderer/            # React app
│   └── shared/              # Constants shared between main/renderer
├── resources/               # Bundled assets (python-backend goes here)
├── electron-builder.yml     # Packaging config
└── electron.vite.config.ts  # Vite config for main/preload/renderer
```
