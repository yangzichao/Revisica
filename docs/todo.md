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

**Session 3 (P4) done:** Deleted dead code (10 `.claude/agents/*.md` files + `agent_assets.py`). Extracted `math_check/` subpackage (pure SymPy math analysis, 4 modules). Extracted `eval/` subpackage (benchmarks + adapters, 10 modules). Benchmark 5/5 PASS.

**Session 4 (ingestion) done:** Three new parsers (markdown, MinerU CLI, Mathpix API). Local-first PDF auto-detection. 29 ingestion tests (pytest). `/api/ingest` endpoint returns full markdown + sections. Spec, learning, architecture docs updated. 5 commits (`e7bd1e6`..`92a7d47`).

**Total: ~5,200 lines Python + ~1,000 lines TS/CSS across 55+ new files. 22 commits.**

---

## What's next

### P1: Make the desktop app actually work end-to-end

- [x] **Backend mode flag** — `backend_mode` in `~/.revisica/config.json` (`cli`/`api`/`auto`). Aliases resolve dynamically. Env var `REVISICA_BACKEND_MODE` override. DMG uses CLI subscription, App Store uses HTTP API.
- [x] **Fix Python 3.9 compat** — `api.py` type syntax (`str | None` → `Optional[str]`), `langgraph` moved to optional dep.
- [x] **API server verified** — health + providers endpoints respond correctly.
- [x] **Electron build verified** — `electron-vite build` compiles. Full GUI test: `cd desktop && npm run dev`.
- [ ] **Settings page (React)** — Provider config UI: API key input for `api` mode, provider status badges. Lower priority if user only uses `cli` mode (subscription).
- [x] **PDF parsers** — `ingestion/mineru_parser.py` (MinerU CLI, local), `ingestion/mathpix_parser.py` (Mathpix API, cloud), `ingestion/markdown_parser.py` (passthrough). Local-first auto-detection. 29 tests.
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
- [ ] **Bundle Pandoc** — Download arm64+x86_64 static binaries (~25 MB each) from GitHub releases. Option A: `pypandoc-binary` in Python venv (PyInstaller picks it up). Option B: `electron-builder extraResources` to `Contents/Resources/bin/pandoc`. GPL-2 OK via subprocess (include license text + source link).
- [ ] **Bundle Marker** — `pip install marker-pdf` (~300 MB with models, no GPU needed). Provides local PDF parsing out of the box. PyInstaller should bundle it with the Python backend.
- [ ] **MinerU — user-installed optional** — Too heavy to bundle (~2+ GB, PyTorch + GPU/MLX). Document as optional: `pip install 'mineru[all]'` (Mac → MLX, Linux → vLLM, Windows → lmdeploy; plain `mineru` falls back to slow CPU Transformers for VLM). App detects via `shutil.which("mineru")` at runtime.
- [ ] **Mathpix — API key only** — No binary to bundle. User provides `MATHPIX_APP_ID` + `MATHPIX_APP_KEY` via Settings page.
- [ ] **PyInstaller packaging** — Freeze Python backend (+ bundled Pandoc + Marker) to `desktop/resources/python-backend`.
- [ ] **electron-builder macOS** — DMG output, code signing (including bundled binaries), notarization.
- [ ] **GitHub Actions CI** — Build → sign → notarize → upload DMG.

### P4: Cleanup + module extraction

- [x] **Delete dead code** — `agent_assets.py` deleted (inlined into writing_review.py), `.claude/agents/*.md` (10 files) deleted.
- [x] **`math_check/` package** — Extracted `math_types`, `math_extraction`, `math_deterministic`, `math_artifacts` into `src/revisica/math_check/`. Pure SymPy, no LLM deps.
- [x] **`eval/` package** — Extracted 6 `benchmark_*.py` + 3 adapters + `hf_datasets.py` into `src/revisica/eval/`.
- [ ] **Unify prompt docs** — Document that dynamic task builders stay in templates.py, static system prompts in agents/definitions/.
- [ ] **Decompose `writing_review.py`** — 800 lines → smaller files as LangGraph nodes take over.

### P5: Math Agent Benchmark + Optimization

- [ ] **ProcessBench baseline** — v0 and v1 prompt comparison on `processbench --split math --limit 10+`
- [ ] **Iterative prompt tuning** — Improve proof-reviewer prompt based on benchmark error analysis
- [ ] **Claude + Codex parity** — Ensure both providers benefit from prompt improvements (Codex instructions mirror agent defs)
- [ ] **Tool-augmented verification** — Validate that Bash/SymPy + WebSearch tools improve `exact_first_error_accuracy`
- [ ] **Literature fact-check agent** — New agent to verify cited references exist and citation context is accurate

### Paused: Refine.ink Recall Gap

**Current:** 83.3% recall (5/6, LLM judge). Resume after desktop foundation is stable.

- [ ] Proof-statement consistency checker (see `docs/specs/proof-statement-checker.md`)
- [ ] Full benchmark re-run with LLM judge (all 4 cases)
- [ ] Algorithm reviewer agent
- [ ] Adaptive section combination budget
- [ ] Cross-provider benchmark
