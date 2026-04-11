# Revisica — TODO

**Last updated:** 2026-04-11 (session 2)

Spec: `docs/specs/desktop-app.md`
Bugs: `docs/bugs.md`
Learning: `docs/learning/`

---

## What's done

**P0 migration: 7/8 substeps complete.** Agent system unified, ingestion wired, provider platform param removed, LangGraph dep added. Benchmark 5/5 PASS.

**Foundation built (Steps 1-7 phase 1):** profiles, ingestion, providers (4 providers), agents (13 definitions + translator), graphs (5 LangGraph graphs), FastAPI server (8 endpoints), Electron + React desktop shell + Academic Revision CSS theme.

**Session 2 done:** Backend mode flag (`cli`/`api`/`auto`) for dual-distribution (DMG + App Store). Fixed Python 3.9 compat (api.py type syntax, langgraph→optional dep). Added logging.warning to all silent exception blocks (bugs.md #4). API server + Electron build verified.

**Total: ~4,800 lines Python + ~1,000 lines TS/CSS across 50+ new files. 17 commits.**

---

## What's next

### P1: Make the desktop app actually work end-to-end

- [x] **Backend mode flag** — `backend_mode` in `~/.revisica/config.json` (`cli`/`api`/`auto`). Aliases resolve dynamically. Env var `REVISICA_BACKEND_MODE` override. DMG uses CLI subscription, App Store uses HTTP API.
- [x] **Fix Python 3.9 compat** — `api.py` type syntax (`str | None` → `Optional[str]`), `langgraph` moved to optional dep.
- [x] **API server verified** — health + providers endpoints respond correctly.
- [x] **Electron build verified** — `electron-vite build` compiles. Full GUI test: `cd desktop && npm run dev`.
- [ ] **Settings page (React)** — Provider config UI: API key input for `api` mode, provider status badges. Lower priority if user only uses `cli` mode (subscription).
- [ ] **PDF parsers** — `ingestion/mathpix_parser.py` (Mathpix API), `ingestion/mineru_parser.py` (MinerU local), `ingestion/marker_parser.py` (Marker fallback). Without these, only `.tex` input works.
- [ ] **Refactor `bootstrap.py`** — Replace `detect_platforms()` with `ProviderRegistry.list_available()` across writing_review.py, math_llm_review.py.

### P2: HITL + Streaming (enables Focus mode + live progress)

- [ ] **LangGraph interrupt nodes** — `interrupt_before` at HITL gates in writing/math subgraphs.
- [ ] **SqliteSaver checkpointer** — `~/.revisica/checkpoints.db`, state survives restarts.
- [ ] **SSE streaming endpoint** — FastAPI SSE consuming `graph.astream_events()`.
- [ ] **Focus API endpoint** — `POST /api/focus/{run_id}` sends FocusRequest, resumes interrupted graph.
- [ ] **Decompose `graphs/writing.py`** — Break into parallel fan-out nodes (roles, section combos, claims). Currently wraps `review_writing_file()` as one node.
- [ ] **Decompose `graphs/unified.py`** — True parallel branches for writing + math lanes.

### P3: Desktop app polish

- [ ] **Paper rendering** — `RevisicaDocument.markdown` → HTML + MathJax math formulas.
- [ ] **Annotation overlay** — Findings as right-side margin notes anchored to sections.
- [ ] **"深挖" (Focus) button** — Per-section deep-dive trigger in Results page.
- [ ] **PyInstaller packaging** — Freeze Python backend to `desktop/resources/python-backend`.
- [ ] **electron-builder macOS** — DMG output, code signing, notarization.
- [ ] **GitHub Actions CI** — Build → sign → notarize → upload DMG.

### P4: Cleanup + module extraction

- [ ] **Delete dead code** — `agent_assets.py`, `.claude/agents/*.md` (10 files).
- [ ] **Unify prompt docs** — Document that dynamic task builders stay in templates.py, static system prompts in agents/definitions/.
- [ ] **`math_check/` package** — Extract math_deterministic.py + friends into independent module.
- [ ] **`eval/` package** — Extract benchmark_*.py into independent evaluation framework.
- [ ] **Decompose `writing_review.py`** — 846 lines → smaller files as LangGraph nodes take over.

### Paused: Refine.ink Recall Gap

**Current:** 83.3% recall (5/6, LLM judge). Resume after desktop foundation is stable.

- [ ] Proof-statement consistency checker (see `docs/specs/proof-statement-checker.md`)
- [ ] Full benchmark re-run with LLM judge (all 4 cases)
- [ ] Algorithm reviewer agent
- [ ] Adaptive section combination budget
- [ ] Cross-provider benchmark
