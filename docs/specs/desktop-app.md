# Spec: Desktop App (Electron + React + Python FastAPI)

**Status:** draft
**Last updated:** 2026-04-11
**Related TODO:** docs/todo.md

## Problem

Revisica is a CLI tool with two limitations:

1. **No GUI.** Non-technical users (academics reviewing papers) cannot use it without command-line knowledge. We need a distributable macOS desktop app (.app / .dmg) with file selection, review configuration, progress monitoring, and report viewing.

2. **Rigid provider access.** The tool currently only works by shelling out to the `codex` and `claude` CLI tools, which require their own subscriptions. Users should also be able to use direct API keys, local models (Ollama), and future API providers — without installing any CLI tool.

## Alternatives Considered

| Approach | Signing/notarization | Auto-update | Production macOS apps | App size |
|---|---|---|---|---|
| **Electron + Python** | Fully automated (electron-builder) | Built-in (Squirrel) | Datasette Desktop, JupyterLab Desktop, Flowfile | 200-400MB |
| Tauri + Python | Broken with sidecar (open bug #11992) | Built-in | None confirmed | 80-150MB |
| pywebview + PyInstaller | Manual, rough edges | None | None public | 40-100MB |
| Swift/SwiftUI rewrite | Best (Xcode native) | Best (Sparkle) | N/A | ~5MB |

**Decision:** Electron + Python. Only approach with confirmed production apps and fully automated macOS distribution pipeline. Swift rewrite rejected because SymPy has no Swift equivalent and the project is iterating rapidly. Tauri is the future migration path once #11992 is fixed — React frontend code is portable.

**Reference implementations:**
- Datasette Desktop: `python-build-standalone` embedded in Electron via `extraResources`
- JupyterLab Desktop: `conda-pack` snapshot in Electron
- Flowfile: PyInstaller-frozen FastAPI + Electron + Vue

## Design

### Architecture

```
Electron app (.app bundle)
├── Main process (Node.js)
│   └── Spawns + manages Python process lifecycle
├── Renderer (React + TypeScript)
│   └── Communicates with Python via REST on localhost
└── Python sidecar (PyInstaller --onefile or python-build-standalone)
    ├── FastAPI server on 127.0.0.1:<port>
    └── All existing revisica code (zero changes to core logic)
```

### Provider abstraction layer (new: `src/revisica/providers/`)

The current `review.py` hardcodes two execution paths (`_run_codex` and `_run_claude`), both via subprocess. This must become a pluggable provider system.

**Current state:**
```
review.py
├── _run_codex()       → subprocess: codex exec ...    (requires codex CLI + subscription)
├── _run_claude()      → subprocess: claude -p ...      (requires claude CLI + subscription)
├── _run_codex_agent() → subprocess: codex exec --full-auto ...
└── _run_claude_agent()→ subprocess: claude -p --agents ...
```

**Target state:**
```
providers/
├── __init__.py        → ProviderRegistry, get_provider()
├── base.py            → abstract BaseProvider with run_prompt() and run_agent()
├── cli_codex.py       → existing subprocess logic (codex CLI + subscription)
├── cli_claude.py      → existing subprocess logic (claude CLI + subscription)
├── api_anthropic.py   → direct Anthropic API (user provides API key)
├── api_openai.py      → direct OpenAI API (user provides API key)
├── ollama.py          → local Ollama (localhost:11434)
└── (future providers)
```

**`BaseProvider` interface:**
```python
class BaseProvider(ABC):
    name: str                          # "claude-cli", "anthropic-api", "openai-api", "ollama", etc.
    display_name: str                  # "Claude (CLI)", "Anthropic API", "OpenAI API", "Ollama", etc.
    auth_type: str                     # "cli-subscription", "api-key", "local", "none"

    @abstractmethod
    def is_available(self) -> bool:
        """Can this provider be used right now? (CLI found / API key set / Ollama running)"""

    @abstractmethod
    def run_prompt(self, prompt: str, model: str | None, timeout: int) -> ReviewResult:
        """Send a prompt, get a response. No tool access."""

    @abstractmethod
    def run_agent(self, task: str, agent_spec: AgentSpec, model: str | None, timeout: int) -> ReviewResult:
        """Run an agent with tool access. Falls back to run_prompt() for providers that don't support agents."""
```

**Provider configuration** (stored in `~/.revisica/config.json` or passed via API):
```json
{
  "providers": {
    "anthropic-api": { "api_key": "sk-ant-...", "default_model": "claude-sonnet-4-20250514" },
    "openai-api": { "api_key": "sk-...", "default_model": "gpt-5" },
    "ollama": { "base_url": "http://localhost:11434", "default_model": "llama3" },
    "claude-cli": { "enabled": true },
    "codex-cli": { "enabled": true }
  }
}
```

**Migration path:** `review.py`'s `_run_provider()` and `_run_provider_agent()` become thin wrappers that call `get_provider(spec.provider).run_prompt()` / `.run_agent()`. All call sites (`writing_review.py`, `math_llm_review.py`, `benchmark_refine.py`) continue to use `ProviderModelSpec` and `ReviewResult` — those types don't change.

**Impact on `model_router.py`:** The default model routes table (`_DEFAULT_ROUTES`) needs entries for new providers. Example: `"anthropic-api": { TASK_MATH_REASONING: "claude-sonnet-4-20250514", ... }`.

**Model family vs provider:** The system uses two model families — **Claude** (Anthropic) and **GPT** (OpenAI). These are the only models used for review tasks. The provider layer is purely the *execution path* to reach those models. The same Claude Sonnet model can be accessed via `claude-cli` (subscription), `anthropic-api` (API key), or in the future via `openrouter` or `groq`.

```
Model families (what we use):     Providers (how we access them):
├── Claude (sonnet, opus, ...)    ├── claude-cli      (CLI subscription)
└── GPT (gpt-5, gpt-5-mini, ...) ├── anthropic-api   (direct API key)
                                  ├── codex-cli       (CLI subscription)
                                  ├── openai-api      (direct API key)
                                  ├── ollama          (local, for experimentation)
                                  └── (future: openrouter, groq, etc.)
```

**Impact on `ProviderModelSpec`:** The `provider` field currently holds `"codex"` or `"claude"`. It will now hold the provider name (e.g. `"anthropic-api"`, `"openai-api"`, `"ollama"`). The `--reviewer-a` CLI syntax becomes `provider[:model]`, e.g. `anthropic-api:claude-sonnet-4-20250514` or `openai-api:gpt-5`. Each provider knows which model family it serves.

**Ollama note:** Ollama is included for local experimentation with open models, not as a primary review provider. The core review pipeline should always prefer Claude or GPT.

**New dependencies:** `anthropic` (Anthropic SDK), `openai` (OpenAI SDK). Both are optional — only needed if the user configures those providers. Use optional imports with clear error messages.

**Desktop app Settings UI:** The Settings page needs:
- Provider list with status (available / needs API key / not installed)
- API key input fields (masked, stored in config)
- Ollama URL configuration
- "Test connection" button per provider
- Provider priority ordering (which to prefer for adjudication, etc.)

**API endpoints (additional):**
| Method | Path | Purpose |
|---|---|---|
| `GET` | `/api/providers` | List all providers with availability status |
| `PUT` | `/api/providers/{name}/config` | Update provider config (API key, URL, etc.) |
| `POST` | `/api/providers/{name}/test` | Test provider connectivity |
| `GET` | `/api/providers/{name}/models` | List available models for a provider |

### Runtime flow

1. Electron launches → spawns Python binary from `Contents/Resources/`
2. Python starts FastAPI server on `127.0.0.1:<port>`
3. Electron polls `/api/health` until 200 (timeout: 30s)
4. Electron opens BrowserWindow pointing to bundled React app
5. React UI calls Python API for all operations
6. On quit → Electron sends SIGTERM to Python, force-kills after 5s

### Python API layer (`src/revisica/api.py`)

Thin FastAPI server wrapping existing functions. No business logic in the API layer.

**Endpoints:**

| Method | Path | Purpose | Backend function |
|---|---|---|---|
| `GET` | `/api/health` | Readiness check | — |
| `GET` | `/api/providers` | Detected provider status | `bootstrap.detect_platforms()` |
| `POST` | `/api/bootstrap` | Install provider assets | `bootstrap.bootstrap()` |
| `POST` | `/api/review` | Start review, return `run_id` | `unified_review.review_unified()` |
| `GET` | `/api/status/{run_id}` | Poll progress | in-memory run state dict |
| `GET` | `/api/results/{run_id}` | Final report + findings | read from `run_dir` on disk |

**Concurrency model:** Reviews run in background threads (reuse existing `ThreadPoolExecutor` pattern). Run state stored in an in-memory `dict[str, RunState]` keyed by `run_id`. The API is single-user (one Electron app), so no persistence or multi-tenant concerns.

**New dependency:** `fastapi`, `uvicorn` added to `pyproject.toml`.

### Progress callback mechanism

Currently `review_unified()`, `review_writing_file()`, and `review_math_file()` are fire-and-forget — they block until completion and return the full result. The GUI needs real-time progress updates.

**Approach:** Add an optional `on_progress: Callable[[ProgressEvent], None] | None = None` parameter to the three orchestrator functions. When provided, they emit `ProgressEvent` at key checkpoints. When `None` (CLI path), behavior is unchanged.

**`ProgressEvent` dataclass** (added to `core_types.py`):
```python
@dataclass
class ProgressEvent:
    lane: str          # "writing", "math", "unified"
    task: str          # "basic-codex", "structure-claude", "deterministic", etc.
    status: str        # "started", "completed", "failed"
    detail: str = ""   # optional human-readable detail
```

**Emit points:**
- `unified_review.py`: lane started, lane completed/failed
- `writing_review.py`: each role+provider task started/completed, self-check started/completed, judge started/completed
- `math_review.py`: extraction done, deterministic checks done, each LLM proof review started/completed

### React frontend

**Views:**

1. **Home** — drag-and-drop or file dialog for `.tex`, venue profile dropdown, provider status badges, "Start Review" button
2. **Review progress** — polls `/api/status/{run_id}` every 1s, shows task list with status icons (pending/running/done/failed), auto-navigates to results on completion
3. **Results** — tabbed view (Summary / Writing / Math), renders Markdown via `react-markdown`, shows output directory path
4. **Settings** — provider detection, bootstrap trigger, version info

**Stack:** React 18, TypeScript, react-router-dom (HashRouter), react-markdown. No CSS framework initially — plain CSS.

### Electron main process

- Dev mode: runs `python -m revisica.api --port <port>`
- Prod mode: runs PyInstaller binary from `process.resourcesPath`
- `titleBarStyle: 'hiddenInset'` for native Mac feel
- External links open in system browser, not in-app

### Packaging & distribution

**Python backend:**
- Option A: `python-build-standalone` + pip install into embedded env (Datasette pattern). More flexible, supports runtime plugin install.
- Option B: `PyInstaller --onefile`. Simpler, single binary, but larger and slower to start.
- Decision deferred to implementation — try PyInstaller first, fall back to python-build-standalone if issues arise.

**Electron app:**
- `electron-builder` for `.dmg` output
- Code signing: requires Apple Developer certificate (`.p12`), configured in `electron-builder.yml`
- Notarization: `@electron/notarize`, requires Apple ID + app-specific password
- Auto-update: `electron-updater` pointing to GitHub Releases
- CI: GitHub Actions workflow — build Python sidecar → build Electron → sign → notarize → upload

**Important:** Python `.so` files must be explicitly listed in the signing config — they are not auto-discovered. `Entitlements.plist` must include `com.apple.security.cs.allow-unsigned-executable-memory`.

### Module interactions

```
cli.py
├── (existing) revisica review → review_unified()    # unchanged behavior, now uses provider registry
└── (new)      revisica serve  → api.py → uvicorn    # new subcommand

providers/
├── ProviderRegistry                  # discovers and manages all providers
├── cli_codex.py, cli_claude.py       # extracted from review.py
├── api_anthropic.py, api_openai.py   # new: direct API access
└── ollama.py                         # new: local model access

review.py
├── _run_provider()       → registry.get(spec.provider).run_prompt()     # refactored
└── _run_provider_agent() → registry.get(spec.provider).run_agent()      # refactored

api.py
├── GET /api/providers      → registry.list_providers()
├── PUT /api/providers/cfg  → update provider config (API keys, URLs)
├── POST /api/review        → threading.Thread(target=review_unified, kwargs={..., on_progress=callback})
├── GET /api/status         → reads from in-memory RunState dict
└── GET /api/results        → reads .md files from run_dir on disk

unified_review.py  (modified: add on_progress param, emit events, pass through to sub-lanes)
writing_review.py  (modified: add on_progress param, emit events at role/task granularity)
math_review.py     (modified: add on_progress param, emit events at sub-module granularity)
core_types.py      (modified: add ProgressEvent dataclass)
model_router.py    (modified: add default routes for anthropic-api, openai-api, ollama)
```

### Directory structure

```
Revisica/
├── src/revisica/
│   ├── providers/              # new: pluggable provider system
│   │   ├── __init__.py         #   ProviderRegistry, get_provider()
│   │   ├── base.py             #   BaseProvider ABC
│   │   ├── cli_codex.py        #   extracted from review.py
│   │   ├── cli_claude.py       #   extracted from review.py
│   │   ├── api_anthropic.py    #   direct Anthropic SDK
│   │   ├── api_openai.py       #   direct OpenAI SDK
│   │   └── ollama.py           #   local Ollama
│   ├── api.py                  # new: FastAPI server
│   ├── provider_config.py      # new: load/save ~/.revisica/config.json
│   └── ...                     # existing files — additive changes only
├── desktop/                    # new: Electron app
│   ├── package.json
│   ├── electron-builder.yml
│   ├── electron.vite.config.ts
│   ├── src/
│   │   ├── main/index.ts
│   │   ├── preload/index.ts
│   │   └── renderer/src/
│   │       ├── App.tsx
│   │       └── pages/
│   └── resources/              # PyInstaller output goes here
└── .github/workflows/
    └── build-desktop.yml
```

## Implementation Plan

### Phase 0: Provider abstraction layer (prerequisite — unblocks everything else)
1. Create `src/revisica/providers/` package with `BaseProvider` ABC and `ProviderRegistry`
2. Extract existing subprocess logic into `cli_codex.py` and `cli_claude.py` providers
3. Implement `api_anthropic.py` (direct Anthropic SDK) and `api_openai.py` (direct OpenAI SDK)
4. Implement `ollama.py` (local Ollama HTTP API)
5. Refactor `review.py` to delegate to `ProviderRegistry` instead of hardcoded `_run_codex` / `_run_claude`
6. Update `model_router.py` with default routes for new providers
7. Add provider config loading/saving (`~/.revisica/config.json`)
8. **Verify:** `revisica review examples/minimal_paper.tex` still works via CLI providers; `revisica benchmark-run --suite math-cases --mode deterministic-only` passes; can run a review with `--reviewer-a anthropic-api:claude-sonnet-4-20250514` if API key is configured

### Phase 1: Python API + progress callbacks
1. Add `ProgressEvent` to `core_types.py`
2. Add `on_progress` parameter to `review_unified()`, `review_writing_file()`, `review_math_file()`
3. Create `src/revisica/api.py` with all endpoints (including provider config endpoints)
4. Add `revisica serve` subcommand to `cli.py`
5. Add `fastapi`, `uvicorn` to `pyproject.toml`
6. **Verify:** `revisica serve` starts, `curl /api/health` returns 200, `POST /api/review` triggers a review, `PUT /api/providers/{name}/config` saves API keys

### Phase 2: Electron shell + React UI
1. Scaffold `desktop/` with electron-vite (React + TypeScript)
2. Implement Electron main process (Python spawn + lifecycle)
3. Build 4 React views (Home, Progress, Results, Settings — Settings includes provider config UI)
4. **Verify:** `npm run dev` opens Electron, can configure providers, trigger and view a full review

### Phase 3: Packaging & distribution
1. PyInstaller spec for Python backend
2. electron-builder config for macOS
3. GitHub Actions CI workflow
4. **Verify:** `npm run build:mac` produces a working `.app`

## Acceptance Criteria

- [ ] `revisica serve` starts FastAPI server, `/api/health` returns 200
- [ ] `POST /api/review` triggers a review and `/api/status` shows real-time progress
- [ ] Existing CLI behavior unchanged (`revisica review` works as before)
- [ ] `revisica benchmark-run --suite math-cases --mode deterministic-only` passes (no regression)
- [ ] `npm run dev` in `desktop/` opens Electron window with working React UI
- [ ] Full review cycle works end-to-end through the desktop app
- [ ] `npm run build:mac` produces a launchable `.app` bundle

## Open Questions

- **Port collision:** What if port 18321 is in use? Use random port and pass to Electron via stdout protocol? Or scan for open port?
- **Multiple windows:** Should each Electron window get its own Python process, or share one? (JupyterLab does one-per-window; Datasette shares one.)
- **File access:** Electron's file dialog returns full paths, but macOS sandboxing may restrict access. Need to test with hardened runtime. May need to disable app sandbox entitlement.
- **Python bundling strategy:** PyInstaller `--onefile` vs `python-build-standalone` — try PyInstaller first, measure startup time and bundle size.
- **Auto-update scope:** Does auto-update cover only the Electron shell, or also the Python backend? If Python is bundled, updating requires a full re-download.
- **API key storage security:** Should API keys be stored in plaintext in `~/.revisica/config.json`, or use macOS Keychain? Keychain is more secure but adds complexity (pyobjc or `security` CLI).
- **Provider SDK bundling:** `anthropic` and `openai` SDKs add to the PyInstaller bundle size. Make them optional imports? Or always bundle?
- **Ollama model discovery:** Ollama exposes `GET /api/tags` to list installed models. Should we auto-discover, or require manual model name entry?
