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

### Priority 1: Zero-risk cleanup

- Remove dead import: `writing_review.py` imports `_run_provider` but does not use it.
- Remove dead function: `_build_role_prompt()` in `writing_review.py`.
- Audit old math prompt builders in `templates.py`:
  - `build_math_proof_review_prompt()`
  - `build_math_proof_adjudication_prompt()`
  - `build_math_proof_self_check_prompt()`
- Keep or remove those functions only after confirming what `benchmark_provenance.py` still hashes.
- Update provenance hashing if prompt-builder removal changes the intended benchmark drift signal.

Definition of done:

- No unused imports or dead helper on the active writing-review path.
- Prompt ownership is clearer than before.
- No behavior change in `writing-review` or `math-review`.

### Priority 2: Fix the temp file leak

- In `review.py`, add cleanup for temp files created by:
  - `_run_codex()`
  - `_run_codex_agent()`
- Use `finally` cleanup around `output_path.unlink(missing_ok=True)`.
- Preserve current behavior when timeout happens and when the output file is absent.

Definition of done:

- No orphan temp files after repeated Codex runs.
- Existing success/timeout fallback behavior is unchanged.

### Priority 3: Split `math_review.py`

Recommended extraction:

- `src/revisica/math_extraction.py`
  - function extraction
  - claim extraction
  - theorem/proof extraction
  - proof blueprint construction
- `src/revisica/math_deterministic.py`
  - SymPy-based claim analysis
  - blueprint analysis
  - issue parsing for deterministic checks
- `src/revisica/math_llm_review.py`
  - provider selection
  - parallel proof review
  - self-check
  - adjudication
  - LLM finding parsing
- `src/revisica/math_artifacts.py`
  - report rendering
  - JSON/Markdown artifact writing

Leave `math_review.py` as the top-level orchestrator that calls these modules.

Definition of done:

- `math_review.py` becomes materially smaller.
- No change to the public function `review_math_file()`.
- Existing benchmark behavior remains stable.

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

### Priority 5: Externalize static agent instructions

Goal:

- Move static system instructions out of inline Python dicts and into role-specific files.

Good candidates:

- `_MATH_AGENT_DEFS` in `math_review.py`
- `_CLAUDE_AGENT_DEFS` in `writing_review.py`
- `_WRITING_SELF_CHECK_AGENT_DEF` in `writing_review.py`
- `_LLM_JUDGE_AGENT_DEF` in `benchmark_refine.py`

Keep in Python:

- Dynamic task builders that inject file paths, JSON payloads, venue profiles, theorem metadata, or findings content.

Definition of done:

- Static instructions are stored as data.
- Dynamic task assembly remains code.
- Prompt iteration becomes easier to review separately from logic changes.

### Priority 6: Extract neutral shared types

Recommended target:

- `src/revisica/core_types.py` or `src/revisica/core/types.py`

Candidate types:

- `ProviderModelSpec`
- `ReviewResult`
- `AgentSpec`
- `FinalReportResult`

Why this is later:

- It is a hygiene improvement and future enabler.
- It does not unblock the highest-friction work as directly as cleanup, temp-file fixes, and `math_review.py` extraction.

Definition of done:

- `model_router.py` no longer depends on `review.py` for core types.
- Shared types have a neutral import home.

### Priority 7: Consolidate adjudicator selection policy

Current locations:

- `review.py`
- `writing_review.py`
- `math_review.py`

Goal:

- Centralize provider preference logic such as "prefer codex if present" into one small utility.

Definition of done:

- One policy source.
- Call sites keep their existing input/output shape.

### Priority 8: Clarify benchmark scope naming

Observation:

- `BenchmarkCaseRun` in `benchmark_framework.py` is math-centric.
- Writing benchmarking currently lives separately in `benchmark_refine.py`.

This is deferred work.

Definition of done:

- Either the framework is explicitly named as math/proof benchmark infrastructure, or its result model becomes truly general.

## Suggested Execution Sequence For The Next Session

1. Clean dead code in `writing_review.py`.
2. Fix temp-file cleanup in `review.py`.
3. Decide the fate of legacy math prompt builders and align `benchmark_provenance.py`.
4. Split `math_review.py` without changing public behavior.
5. Refactor `benchmark_framework.py` into suite/mode dispatch structures.
6. Externalize static agent instructions.
7. Extract shared types.
8. Consolidate adjudicator selection.

## Safety Checks After Each Step

- Run targeted grep to confirm the old path is really gone.
- Run the smallest relevant command after each change, not one giant end-to-end sweep only at the end.
- For cleanup steps, verify imports, dead code removal, and artifact paths.
- For `math_review.py` extraction, compare generated report structure before and after.
- For benchmark refactors, verify at least one suite still writes the same summary artifacts.

## Good First Commands For The Next Session

```bash
git status --short
rg -n "_run_provider|_build_role_prompt|build_math_proof_review_prompt|build_math_proof_adjudication_prompt|build_math_proof_self_check_prompt" src/revisica
python -m compileall src/revisica
```

## Session Kickoff Prompt

Use this to start the next implementation session:

```text
Work from docs/architecture-refactor-todo.md.
Start with Priority 1 and Priority 2 only:
- remove dead code on the writing-review path
- fix temp file cleanup in review.py

Do not redesign the system yet.
Keep behavior stable.
After edits, run the smallest verification needed and summarize exactly what changed.
```
