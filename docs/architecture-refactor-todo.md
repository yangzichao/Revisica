# Revisica Architecture Refactor TODO

## Background

This TODO captures the merged architecture diagnosis from the April 7, 2026 review pass.

The high-level conclusion is:

- The semantic architecture is mostly correct.
- The main problems are accumulation effects, not conceptual mistakes.
- The next work should focus on cleanup and extraction, not redesign.

Confirmed strengths:

- CLI command dispatch is mostly clean and thin.
- The top-level split between writing review, math review, unified review, and benchmarks is the right boundary.
- Provider execution is already abstracted behind shared result/spec types.
- `model_router.py` cleanly separates task type from model choice.
- `section_combiner.py` and `claim_extractor.py` are good examples of bounded modules.

Confirmed problems:

- `src/revisica/math_review.py` is too large and mixes extraction, analysis, LLM orchestration, adjudication, and artifact writing.
- `src/revisica/benchmark_framework.py` has multiple suite/mode extension branches that will get worse as more suites or modes are added.
- There is a temp-file leak in Codex subprocess execution.
- Some dead code and legacy prompt paths remain after the move to agent-task builders.
- Static agent instructions are split between inline Python dicts and external Codex markdown files.

Important framing:

- This is not a rewrite.
- Most of the needed work is mechanical extraction and cleanup.
- The goal is to improve iteration speed for benchmark and prompt work without changing external behavior unless explicitly intended.

## Ground Rules

- Preserve current CLI behavior unless the task explicitly changes it.
- Prefer small, verifiable refactors over broad redesign.
- Do not mix prompt-content changes with structural changes in the same patch unless necessary.
- When removing legacy code, verify whether it is still used for provenance or hashing before deleting it.
- Keep benchmark outputs and artifact formats stable unless a task explicitly updates them.

## Priority Order

### Priority 1: Zero-risk cleanup — DONE

All items completed:

- ~~Remove dead import: `writing_review.py` imports `_run_provider` but does not use it.~~
- ~~Remove dead function: `_build_role_prompt()` in `writing_review.py`.~~
- ~~Audit old math prompt builders in `templates.py`.~~
- ~~Update provenance hashing.~~

### Priority 2: Fix the temp file leak — DONE

Completed: Both `run_prompt()` and `run_agent()` in `providers/cli_codex.py` use `finally: output_path.unlink(missing_ok=True)`.

### Priority 3: Split `math_review.py` — DONE

Completed: `math_review.py` reduced from ~800 to 127 lines (pure orchestrator). Extracted into two subpackages:

- `math_check/` (4 modules): types, extraction, deterministic analysis, artifact rendering (pure SymPy)
- `math_llm/` (3 modules): `task.py` (prompt construction), `parse.py` (output parsing), `review.py` (orchestration)

Public API `review_math_file()` unchanged.

### Priority 4: Replace benchmark branch sprawl

Targets in `benchmark_framework.py`:

- suite loader in `run_benchmark()`
- mode dispatcher in `_run_case()`
- suite metrics logic in `_compute_suite_metrics()`

Recommended direction:

- Introduce a suite registry abstraction with per-suite loaders and metric computation.
- Replace mode branching with a mode-keyed dispatch table.
- Make `"all"` explicit rather than an implicit `else` fallback.

Definition of done:

- Adding a new suite does not require touching multiple existing `if/elif` ladders.
- Adding a new mode touches one dispatch structure, not a long conditional chain.

### Priority 5: Externalize static agent instructions — DONE

Completed: 14 agent definitions in `agents/definitions/` (writing_basic, writing_structure, writing_venue, writing_self_checker, writing_judge, proof_reviewer, proof_self_checker, proof_adjudicator, claim_verifier, notation_tracker, formula_cross_checker, polish_agent, refine_eval_judge). All inline `_*_AGENT_DEFS` dicts removed. Dynamic task builders remain in code.

### Priority 6: Extract neutral shared types — DONE

Completed: `core_types.py` exists with `ProviderModelSpec`, `ReviewResult`, `AgentSpec`, `FinalReportResult`. `model_router.py` no longer depends on `review.py` for types.

### Priority 7: Consolidate adjudicator selection policy — DONE

Completed: `adjudication_policy.py` centralizes provider preference logic. One policy source, call sites unchanged.

### Priority 8: Clarify benchmark scope naming

Observation:

- `BenchmarkCaseRun` in `benchmark_framework.py` is math-centric.
- Writing benchmarking currently lives separately in `benchmark_refine.py`.

This is deferred work.

Definition of done:

- Either the framework is explicitly named as math/proof benchmark infrastructure, or its result model becomes truly general.

## Remaining Work

Next session should tackle:

1. **Priority 4:** Refactor `eval/framework.py` — introduce suite registry and mode dispatch table.
2. **Priority 8:** Clarify benchmark scope naming (low priority, can defer further).

Blocked on other work:

- Decompose `writing_review.py` (806 lines) — depends on LangGraph graph decomposition.
- Remove `agents/translators.py` bridge — depends on provider interface refactor to accept `AgentDefinition` directly.
