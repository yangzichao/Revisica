# Bugs & Cleanup

**Filed:** 2026-04-11
**Last verified:** 2026-04-11 (commit `681da94`)

## Fixed

### 1. `.gitignore` stale paths after benchmark rename — FIXED

**Commit:** `681da94` → fixed in this session
**Was:** 4 dead `.gitignore` rules pointing to old `*_cases` paths
**Fix:** Updated to `benchmarks/math/runs/`, `benchmarks/writing/runs/`, etc.

### 3. `agents/codex/` missing 2 agent definitions — FIXED

**Commit:** this session
**Was:** `refine-eval-judge.md` and `writing-self-checker.md` missing from Codex agents
**Fix:** Created both files with content matching the Claude JSON equivalents.

## Open

### 2. Three redundant agent definition locations — FIXED

**Fixed:** 2026-10-15
**Was:** Codex CLI read its system prompt from `agents/codex/*.md`, which had drifted far from `src/revisica/agents/definitions/*.py` (difflib similarity 0.20 for `math-proof-reviewer`), and versioned agents (`math-proof-reviewer-vN`) had no `.md` at all, so Codex ran them without a system prompt. `agents/` sat outside the package, so the frozen DMG had neither the prompts nor `findings.schema.json`. Claude CLI separately sent `{"instructions": ...}` to `--agents`; Claude Code 2.1.301 rejects that with `Invalid --agents configuration` (it requires `description` + `prompt`).
**Fix:** `AgentSpec` now carries `system_prompt` / `description` / `tools`, and all four providers read them. `agents/claude/` and `agents/codex/` are deleted; the schema moved to `src/revisica/agents/output_schemas/` (shipped as package data). Benchmark provenance now hashes the Python proof-agent modules, so `math_proof_review` hashes differ from older registry rows.

### 4. Silent exception swallowing — no logging on failure — FIXED

**Commit:** session 2 (2026-04-11)
**Was:** 5 bare `except Exception:` blocks with no logging.
**Fix:** Added `logging.warning()` with `exc_info=True` to all 5 locations. JSON parse fallback uses `logging.debug()` (high-frequency, noise reduction).

### 5. `review.py` `_run_provider()` takes unused `platform` parameter — FIXED

**Commit:** `9cdf0ef` (P0.5)
**Was:** `platform: PlatformStatus` parameter accepted but ignored in `_run_provider()` and `_run_provider_agent()`.
**Fix:** Removed dead parameter and updated all call sites.
