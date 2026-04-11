# Spec: Desktop App (Electron + React + Python FastAPI)

**Status:** in-progress
**Last updated:** 2026-04-11
**Related TODO:** docs/todo.md

## Problem

Revisica is a CLI tool. Non-technical users (academics reviewing papers) cannot use it without command-line knowledge. We need a distributable macOS desktop app (.app / .dmg) that provides a GUI for file selection, review configuration, progress monitoring, and report viewing.

## Design

**Architecture:** Electron (React + TypeScript frontend) + Python FastAPI backend as a sidecar process.

**Why Electron + Python:**
- Only approach with confirmed production macOS apps (Datasette Desktop, JupyterLab Desktop)
- Fully automated code signing + notarization via electron-builder
- Built-in auto-update (electron-updater / Squirrel)
- 100% Python code reuse — FastAPI wraps existing functions
- React frontend is portable to Tauri when its macOS sidecar notarization bug (#11992) is fixed

**Runtime flow:**
1. Electron launches → spawns PyInstaller-bundled Python binary
2. Python starts FastAPI server on `localhost:<port>`
3. Electron waits for `/api/health` → opens BrowserWindow
4. React UI communicates with Python via REST API
5. On quit → Electron kills Python process

**API endpoints:**
- `GET /api/health` — readiness check
- `GET /api/providers` — detected provider status
- `POST /api/bootstrap` — install provider assets
- `POST /api/review` — start a review (returns run_id)
- `GET /api/status/{run_id}` — progress polling
- `GET /api/results/{run_id}` — final report + findings

**UI views:**
1. Home — file picker, venue profile, provider config
2. Review progress — live task status per lane/role
3. Results — rendered Markdown report with expandable sections
4. Settings — provider detection, bootstrap

## Implementation Plan

1. Scaffold `desktop/` with electron-vite (React + TypeScript)
2. Create `src/revise_agent/api.py` (FastAPI server wrapping existing functions)
3. Add progress callback mechanism to unified/writing/math review
4. Wire Electron main process to spawn/manage Python sidecar
5. Build React frontend (4 views)
6. PyInstaller packaging for Python backend
7. electron-builder config for macOS distribution

## Acceptance Criteria

- [ ] `revise-agent serve` starts FastAPI server, `/api/health` returns 200
- [ ] `POST /api/review` triggers a review and `/api/status` shows real-time progress
- [ ] Existing CLI behavior unchanged (`revise-agent review` works as before)
- [ ] `revise-agent benchmark-run --suite math-cases --mode deterministic-only` passes
- [ ] `npm run dev` in `desktop/` opens Electron window with working UI
- [ ] Full review cycle works end-to-end through the desktop app
- [ ] `npm run build` produces a launchable `.app` bundle
