# Spec: Revisica Desktop App — Full Architecture

**Status:** approved
**Last updated:** 2026-04-11
**Plan file:** `~/.claude/plans/immutable-dazzling-mochi.md`

## Problem

Revisica is a CLI tool with three limitations:

1. **No GUI.** Non-technical users cannot use it without command-line knowledge.
2. **Rigid provider access.** Only works via `codex`/`claude` CLI subprocess calls. Need API key support.
3. **No input flexibility.** Only reads raw `.tex`. Users have PDFs.

## Solution: 10 independent modules

```
src/revisica/
├── ingestion/       PDF/tex → RevisicaDocument (standardized Markdown + LaTeX math)
├── providers/       Pluggable provider abstraction (CLI, API key, local)
├── profiles/        Review modes: Polish / Review / Focus
├── agents/          Unified agent definitions (one definition, all providers)
├── graphs/          LangGraph orchestration (dynamic DAG, HITL, streaming)
├── math_check/      SymPy deterministic checks (existing, extracted)
├── eval/            Benchmark evaluation + LLM judge + metrics
├── api/             FastAPI server wrapping graph execution
├── renderer/        npm package: RevisicaDocument → HTML (MathJax)
└── desktop/         Electron shell (React + TypeScript)
```

## Key decisions

- **Desktop framework:** Electron + Python (FastAPI sidecar). Only approach with production macOS apps (Datasette Desktop, JupyterLab Desktop). Tauri is future migration path.
- **Orchestration:** LangGraph. Only framework with multi-provider + HITL + dynamic routing + streaming.
- **PDF parsing:** Mathpix API (best quality) + MinerU (open-source, GPU) + Marker (fallback). User chooses.
- **Intermediate format:** Markdown + LaTeX math (RevisicaDocument). All parsers normalize to this.
- **Model families:** Claude + GPT only. Provider = execution path, not model choice.
- **Review modes:** Polish (single agent, writing only) / Review (full deep analysis) / Focus (section-level deep dive, HITL-triggered).
- **Agent definitions:** One definition per agent, provider translators handle format differences.
- **Design theme:** Claude Code warm palette + vintage academic paper aesthetic.

## Implementation phases

1. **Profiles + Ingestion** — RevisicaDocument format, PDF parsers, review config
2. **Provider package** — Extract CLI providers, add registry
3. **API providers** — Anthropic/OpenAI SDK with tool-use loops
4. **LangGraph graphs** — Polish → Math → Writing → Unified → Focus
5. **HITL + streaming** — Interrupt nodes, SqliteSaver, SSE
6. **Desktop app** — FastAPI + Electron + React + renderer

## Code conventions

- Single Python file ≤ 300 lines; split when larger
- Single React component ≤ 200 lines; one component per file
- Variable names: descriptive, longer is better than unclear (`provider_model_spec` not `pms`)
- One file = one responsibility; filename = responsibility

## Acceptance criteria

See plan file for detailed verification steps per phase.
