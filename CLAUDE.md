# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Setup and Installation

```bash
python3 -m venv .venv && . .venv/bin/activate
python -m pip install .
revise-agent bootstrap
```

No Makefile. All development commands go through the `revise-agent` CLI (entry point: `src/revise_agent/cli.py`).

## Running the Tool

```bash
# Unified (writing + math concurrently)
revise-agent review examples/minimal_paper.tex
revise-agent review examples/minimal_paper.tex --venue-profile econ-top5 --llm-proof-review

# Individual lanes
revise-agent writing-review examples/minimal_paper.tex --reviewer-a codex:gpt-5 --reviewer-b claude:sonnet
revise-agent math-review examples/minimal_paper.tex --llm-proof-review --targets codex claude
```

## Running Benchmarks

```bash
# Local suites
revise-agent benchmark-math
revise-agent benchmark-writing

# Unified runner (suites: math-cases, proofnet, proofbench, processbench, all)
# Modes: deterministic-only, single-agent, single-agent-self-check, multi-agent-cross-check, hybrid-single, hybrid-cross
revise-agent benchmark-run --suite math-cases --mode deterministic-only
revise-agent benchmark-run --suite proofnet --mode single-agent --limit 1 --reviewer codex:gpt-5

# Refine.ink benchmark (primary eval for recall against paper comments)
revise-agent benchmark-refine

# Benchmark history
revise-agent benchmark-history
```

Quickest sanity check after a change: `revise-agent benchmark-run --suite math-cases --mode deterministic-only`

## Architecture

ReviseAgent converts a LaTeX paper into reviewable units and runs them through two independent lanes in parallel:

```
LaTeX file → split into units → [writing lane | math lane] → merge findings → final report
```

**Writing lane** (`writing_review.py`):
- Extracts sections and generates section combinations (pairs/triples)
- Runs 3 specialist roles in parallel via `ThreadPoolExecutor` (up to 12 workers): `basic` (grammar/clarity), `structure` (logic/flow), `venue` (style/fit)
- Optional self-check and judge/adjudication layers
- Calls providers via `review.py`, which shells out to the `codex` or `claude` CLI

**Math lane** (`math_review.py` → four sub-modules):
- `math_extraction.py`: parse functions, claims, theorem/proof blocks from LaTeX
- `math_deterministic.py`: SymPy-based symbolic checks (integrals, average-value claims, continuity/domain)
- `math_llm_review.py`: multi-provider proof-obligation review with optional self-check and adjudication
- `math_artifacts.py`: render JSON/Markdown reports

**Provider execution** (`review.py`): shared layer that invokes `codex` and `claude` CLIs as subprocesses. Model routing is centralized in `model_router.py`—task type determines which provider/model spec to use.

**Benchmarking** (`benchmark_framework.py`, `benchmark_refine.py`): `benchmark_framework.py` runs math-oriented suites across modes; `benchmark_refine.py` is the Refine.ink adapter with a claim-by-claim verifier and LLM judge. Provenance (git commit, prompt hashes, pass/fail) is recorded in `benchmarks/registry.jsonl`.

**Agent definitions**: `.claude/agents/` holds markdown files defining writing and math specialist agents. Static system instructions should live in these files; dynamic task builders (injecting file paths, findings content, venue profiles) remain in Python.

## Key Source Files

| File | Role |
|---|---|
| `cli.py` | Command dispatch (thin) |
| `unified_review.py` | Concurrent writing + math orchestration |
| `writing_review.py` | Writing lane orchestration (846 lines, has known dead code—see Priority 1 in `docs/architecture-refactor-todo.md`) |
| `math_review.py` | Math lane orchestrator (calls 4 sub-modules) |
| `review.py` | Shared provider execution; shells out to `codex`/`claude` CLIs (known temp-file leak—see Priority 2) |
| `benchmark_framework.py` | Unified benchmark runner |
| `benchmark_refine.py` | Refine.ink benchmark adapter |
| `templates.py` | All prompt templates |
| `model_router.py` | Task-type → provider/model selection |
| `core_types.py` | `ProviderModelSpec`, `ReviewResult`, `AgentSpec` dataclasses |

## Output Structure

- Reviews: `reviews/<stem>-unified-<timestamp>/summary.md` (+ `writing/`, `math/` subdirs)
- Benchmarks: `benchmarks/runs/<suite>-<mode>-<timestamp>/benchmark_summary.md`
- Provenance registry: `benchmarks/registry.jsonl`

## Known Issues and Refactoring Plan

See `docs/architecture-refactor-todo.md` for the full ordered refactor plan. Priority areas:
1. Dead code in `writing_review.py` (`_run_provider` import, `_build_role_prompt`)
2. Temp-file leak in `review.py` Codex subprocess execution
3. `math_review.py` is oversized—extraction, deterministic, LLM, and artifact logic are already split into sub-modules but the orchestrator still carries too much
4. `benchmark_framework.py` has suite/mode `if/elif` branching that needs a registry/dispatch table

**Ground rules for refactoring**: preserve current CLI behavior unless explicitly changing it; do not mix prompt-content changes with structural changes; verify benchmark artifact format is stable after each change.

## Benchmark Reporting

When recording benchmark results, follow the format in `docs/benchmark-reports/` (see memory: `feedback_benchmark_report_format.md`):
- File: `docs/benchmark-reports/YYYY-MM-DD-<name>.md`
- Must include: git commit ID, exact commands run, artifact paths
