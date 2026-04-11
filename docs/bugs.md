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

### 2. Three redundant agent definition locations

**Severity:** MEDIUM — maintenance burden, confusion about source of truth
**Status:** Partially addressed by `src/revisica/agents/definitions/` (new unified system)

Two active locations remain (`.claude/agents/` deleted in P4, `agent_assets.py` deleted):

| Location | Format | Files | Status |
|---|---|---|---|
| `agents/claude/*.json` | JSON | 12 | Active — loaded by unified agent registry |
| `agents/codex/*.md` | Markdown | 13 | Active — used by Codex CLI |
| `src/revisica/agents/definitions/*.py` | Python | 11 | **New** — unified definitions (not yet wired) |

**Plan:** Once `agents/translators/` is implemented, the `agents/claude/` and `agents/codex/` directories become generated output. The unified definitions in `src/revisica/agents/definitions/` become the single source of truth.

### 4. Silent exception swallowing — no logging on failure — FIXED

**Commit:** session 2 (2026-04-11)
**Was:** 5 bare `except Exception:` blocks with no logging.
**Fix:** Added `logging.warning()` with `exc_info=True` to all 5 locations. JSON parse fallback uses `logging.debug()` (high-frequency, noise reduction).

### 5. `review.py` `_run_provider()` takes unused `platform` parameter — FIXED

**Commit:** `9cdf0ef` (P0.5)
**Was:** `platform: PlatformStatus` parameter accepted but ignored in `_run_provider()` and `_run_provider_agent()`.
**Fix:** Removed dead parameter and updated all call sites.
