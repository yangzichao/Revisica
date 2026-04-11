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

Three locations still exist:

| Location | Format | Files | Status |
|---|---|---|---|
| `agents/claude/*.json` | JSON | 12 | Active — loaded by `agent_assets.py` |
| `agents/codex/*.md` | Markdown | 13 | Active — used by Codex CLI |
| `.claude/agents/*.md` | Markdown | 10 | Dead — not loaded by any code |
| `src/revisica/agents/definitions/*.py` | Python | 11 | **New** — unified definitions (not yet wired) |

**Plan:** Once `agents/translators/` is implemented (P1 in TODO), the `agents/claude/` and `agents/codex/` directories become generated output. `.claude/agents/` can be deleted. The unified definitions in `src/revisica/agents/definitions/` become the single source of truth.

### 4. Silent exception swallowing — no logging on failure

**Severity:** LOW — correct fallback behavior, but failures are invisible

| File | Line | Context |
|---|---|---|
| `writing_review.py` | 385 | Writing self-check failure — keeps original findings |
| `math_llm_review.py` | 390 | Math self-check failure — falls back to unchecked |
| `math_llm_review.py` | 447 | Math adjudication failure — falls back to raw findings |
| `math_llm_review.py` | 721 | LLM issue parsing failure — skips issue |
| `math_extraction.py` | 29 | LaTeX parsing failure — skips block |

All have correct fallback behavior. The problem is zero visibility — if self-check is consistently broken, no one would know.

**Fix needed:** Add `logging.warning(...)` to each bare `except Exception:` block.

### 5. `review.py` `_run_provider()` takes unused `platform` parameter

**Severity:** LOW — no runtime impact, just confusing API
**Filed:** 2026-04-11

After the provider registry refactor, `_run_provider()` and `_run_provider_agent()` in `review.py` still accept a `platform: PlatformStatus` parameter that they completely ignore. All call sites still pass it.

```python
# review.py:162 — platform is accepted but never used
def _run_provider(provider_name, platform, prompt, timeout_seconds, model=None):
    provider = get_provider(provider_name)
    return provider.run_prompt(prompt, model=model, timeout_seconds=timeout_seconds)
```

**Fix:** Remove `platform` parameter from `_run_provider()` and `_run_provider_agent()`, update all call sites in `writing_review.py`, `math_llm_review.py`, `benchmark_refine.py`, and `review.py` itself. This is a mechanical refactor but touches many files.

**Blocked by:** Agent translators (P1) — once translators are done, the call sites will be rewritten anyway.
