# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Setup and Installation

```bash
python3 -m venv .venv && . .venv/bin/activate
python -m pip install .
revisica bootstrap
```

Only runtime dependency is `sympy>=1.13`. No Makefile — all development commands go through the `revisica` CLI (entry point: `src/revisica/cli.py`).

## Running the Tool

```bash
# Unified (writing + math concurrently)
revisica review examples/minimal_paper.tex
revisica review examples/minimal_paper.tex --venue-profile econ-top5 --llm-proof-review

# Individual lanes
revisica writing-review examples/minimal_paper.tex --reviewer-a codex:gpt-5 --reviewer-b claude:sonnet
revisica math-review examples/minimal_paper.tex --llm-proof-review --targets codex claude
```

Role arguments use the `provider[:model]` format, e.g. `codex:gpt-5` or `claude:sonnet`. When no model is specified, `model_router.py` auto-selects based on task type (math reasoning -> opus/gpt-5, writing -> sonnet/gpt-5).

Supported venue profiles: `general-academic`, `econ-general-top`, `econ-top5`, `econ-theory`, `econ-empirical`, `econ-applied`.

## Running Benchmarks

```bash
# Local suites
revisica benchmark-math
revisica benchmark-writing

# Unified runner (suites: math-cases, proofnet, proofbench, processbench, all)
# Modes: deterministic-only, single-agent, single-agent-self-check, multi-agent-cross-check, hybrid-single, hybrid-cross
revisica benchmark-run --suite math-cases --mode deterministic-only
revisica benchmark-run --suite proofnet --mode single-agent --limit 1 --reviewer codex:gpt-5

# Refine.ink benchmark (primary eval for recall against paper comments)
revisica benchmark-refine
revisica benchmark-refine --reviewer-a claude --use-llm-judge --llm-judge claude:sonnet --timeout-seconds 600

# Benchmark history
revisica benchmark-history
```

Quickest sanity check after a change: `revisica benchmark-run --suite math-cases --mode deterministic-only`

Unit tests: `pytest tests/` (29 ingestion tests). For end-to-end correctness: `revisica benchmark-run --suite math-cases --mode deterministic-only`.

## Architecture

Revisica ingests academic papers (`.tex`, `.pdf`, `.md`, `.mmd`) through format-specific parsers into a common `RevisicaDocument`, then runs two independent review lanes in parallel:

```
any format → ingestion (parser → normalize) → RevisicaDocument → [writing lane | math lane] → merge → report
```

For detailed architecture documentation, see `docs/current-architecture.md`.

## Key Source Files

| File | Role |
|---|---|
| `cli.py` | Command dispatch (thin) |
| `ingestion/` | **Subpackage:** multi-format parsers (markdown, MinerU, Mathpix, Pandoc, tex-basic, Marker) + normalize → `RevisicaDocument` |
| `unified_review.py` | Concurrent writing + math orchestration |
| `writing_review.py` | Writing lane orchestration |
| `math_review.py` | Math lane orchestrator |
| `math_llm_review.py` | Multi-provider proof review + adjudication |
| `math_check/` | **Subpackage:** types, extraction, deterministic analysis, artifact rendering (pure SymPy, no LLM deps) |
| `review.py` | Shared provider execution; delegates to `providers/` registry |
| `templates.py` | All prompt templates and venue profile definitions |
| `model_router.py` | Task-type -> provider/model selection |
| `core_types.py` | `ProviderModelSpec`, `ReviewResult`, `AgentSpec` dataclasses |
| `adjudication_policy.py` | Provider preference logic for adjudication |
| `section_combiner.py` | Section extraction and combination generation |
| `claim_extractor.py` | Per-paragraph/footnote claim extraction and verification tasks |
| `eval/` | **Subpackage:** benchmark framework, math/writing/refine benchmarks, provenance, HF dataset adapters |
| `bootstrap.py` | CLI/asset detection and installation for codex/claude platforms |

## Environment Variables

| Variable | Purpose |
|---|---|
| `REVISICA_BACKEND_MODE` | Provider backend: `cli` (DMG/subscription), `api` (App Store/key), `auto` (default) |
| `REVISICA_CODEX_HOME` | Override Codex config home (default: `~/.codex`) |
| `REVISICA_CLAUDE_HOME` | Override Claude config home (default: `~/.claude`) |
| `REVISICA_RUNTIME_HOME` | Override `$HOME` for subprocess execution |

## Output Structure

- Reviews: `reviews/<stem>-unified-<timestamp>/summary.md` (+ `writing/`, `math/` subdirs)
- Benchmarks: `benchmarks/runs/<suite>-<mode>-<timestamp>/benchmark_summary.md` (framework runs), `benchmarks/<suite>/runs/` (per-suite runs)
- Provenance registry: `benchmarks/registry.jsonl`
- Curated reports: `benchmarks/reports/`

## Documentation Map

| What | Where |
|---|---|
| Task priorities | `docs/todo.md` |
| Feature specs | `docs/specs/` |
| Experiment learnings | `docs/learning/` (see `README.md` for index) |
| Architecture details | `docs/current-architecture.md` |
| Refactoring plan | `docs/architecture-refactor-todo.md` |
| Benchmark reports | `benchmarks/reports/` |
| Agent definitions | `.claude/agents/` |

## Conventions

**Ground rules for refactoring**: preserve current CLI behavior unless explicitly changing it; do not mix prompt-content changes with structural changes; verify benchmark artifact format is stable after each change.

**Benchmark reporting format**: `benchmarks/reports/YYYY-MM-DD-<name>.md` — must include git commit ID, exact commands run, artifact paths.

**Learning file format**: `docs/learning/YYYY-MM-DD-<slug>.md` — must include date, commit, observation, lesson, architecture implications.

**Spec file format**: `docs/specs/<feature-name>.md` — must include status, problem, design, implementation plan, acceptance criteria.
