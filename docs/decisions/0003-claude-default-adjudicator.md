# 0003. Prefer Claude as default adjudicator and judge

**Status:** Accepted
**Date:** 2026-06-10
**Commit:** pending (review-engine cleanup pass on top of `5e5b425`)

## Context

When several providers produce findings and no explicit judge/adjudicator
spec is given, Revisica picks one provider to do the final merge. This
policy is centralized in [adjudication_policy.py](../../src/revisica/adjudication_policy.py)
and used by three call sites: math proof adjudication
(`math_llm/review.py`), the writing-lane default judge (`writing/judge.py`),
and the Refine.ink benchmark LLM judge (`eval/refine.py`).

The historical default was `codex`, hardcoded as a parameter default. That
predates benchmark evidence: on ProcessBench (detecting the first erroneous
step in math proofs), Claude scored **58%** vs Codex **27%** — and
adjudication is dominated by exactly that kind of careful step-checking.
The Codex deprioritization is also recorded in project memory and reflected
in `model_router.py`'s math-task routing.

## Decision

**The default preferred provider for adjudication/judging is `claude`.**

- `adjudication_policy.DEFAULT_PREFERRED_PROVIDER = "claude"`.
- The `REVISICA_PREFERRED_ADJUDICATOR` environment variable overrides it
  (e.g. `REVISICA_PREFERRED_ADJUDICATOR=codex` restores the old behavior).
- Explicit `--judge` / adjudicator specs always win; the policy only
  applies when no spec is given.
- The preference is a *tie-breaker among providers that actually produced
  results*: if only Codex results exist, Codex is still picked.

## Consequences

**Easier:**
- Default adjudication quality aligns with measured math-checking
  capability instead of an arbitrary historical default.
- Provider preference is configurable per environment without code change.

**Harder / newly risky:**
- This is a deliberate behavior change: runs that previously adjudicated
  with Codex (when both providers were available and no judge was
  specified) now adjudicate with Claude. Cross-run comparisons of older
  benchmark results must account for it.
- Claude subscription/rate limits absorb more of the adjudication load.
