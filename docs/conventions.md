# Code Conventions

Standards for `src/revisica/`. These codify the patterns the June 2026
cleanup pass converged on; new code should follow them, and refactors
should move old code toward them.

## Module layout

- **Small files, split early.** When a module grows past roughly 300
  lines or starts mixing responsibilities, split it into a feature
  subpackage (as `math_check/`, `math_llm/`, `writing/`, `ingestion/`,
  `jobs/`, and `eval/` already are).
- **One subpackage per lane/feature**, with a `__init__.py` that
  re-exports the public API and a docstring listing each module's role.
  Callers outside the subpackage import from the package root
  (`from .writing import review_writing_file`) unless they need a
  specific helper (`from .writing.findings import extract_findings_payload`).
- **Orchestrators stay thin.** `math_review.py`, `unified_review.py`, and
  `writing/entry.py` wire stages together; the stages themselves live in
  bounded modules.

## Naming

- **Descriptive over short.** `resolve_reviewer_specs`, not `resolve`.
- **No duplicate public names across modules.** Two functions named
  `extract_claims` caused real confusion; they are now
  `extract_math_claims` (SymPy claims, `math_check/`) and
  `extract_paragraph_claims` (writing-lane claims, `claim_extractor.py`).
  When a name collision appears, rename both to say what they extract.
- **Underscore prefix means module-private.** If another module needs a
  helper, de-underscore it and move it to the right module — never import
  `_private` names across modules.

## LLM integration

- **`providers/execution.py:run_provider_agent()` is the single LLM call
  point.** All lanes, judges, self-checkers, and adjudicators go through
  it. Never shell out to `codex`/`claude` directly from lane code.
- **Static system prompts live in `agents/definitions/`**, one file per
  agent. Dynamic task prompts (file paths, venue profile, findings JSON)
  are built in lane code (`writing/agent_tasks.py`, `math_llm/task.py`).
  Don't blur the boundary: a definition file must not contain per-run
  data, and lane code must not duplicate an agent's standing instructions.
- **Model choice goes through `model_router.py`**
  (`resolve_model_for_role` / `resolve_model_for_task`). Lane code never
  hardcodes model names.
- **Provider preference goes through `adjudication_policy.py`.** Default
  is `claude` (ProcessBench: Claude 58% vs Codex 27%); override with
  `REVISICA_PREFERRED_ADJUDICATOR`. See ADR 0003.

## Degraded paths must be visible

Every fallback (failed self-check, failed adjudication, cross-check with
fewer than 2 providers, judge failure) must append a human-readable
message to the run's `warnings` list, which is rendered into
`summary.md`. Logging alone is not enough — users read the summary, not
the server log.

## Prompt and structural changes stay separate

From the refactor ground rules (CLAUDE.md), still binding:

- Preserve current CLI behavior unless explicitly changing it.
- Do not mix prompt-content changes with structural changes in one patch.
- Keep benchmark artifact formats stable; verify with
  `revisica benchmark-run --suite math-cases --mode deterministic-only`
  after structural changes.
- Prompt content is provenance-hashed (`eval/provenance.py`). When moving
  a prompt builder or agent definition, update the hash sources in the
  same patch so `registry.jsonl` records stay meaningful.

## Verification loop for refactors

After any structural change, run all three:

1. Import smoke: `python -c "import revisica.cli, revisica.unified_review, ..."`.
2. Unit tests: `pytest tests/ --ignore=tests/test_extraction.py`
   (`test_extraction.py` needs `hypothesis`, not installed in all envs).
3. Behavior check: `revisica benchmark-run --suite math-cases --mode deterministic-only`
   — all cases must PASS.
