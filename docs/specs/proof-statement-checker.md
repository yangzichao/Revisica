# Spec: Proof-Statement Consistency Checker

**Status:** draft
**Last updated:** 2026-04-11
**Related TODO:** docs/todo.md — "Proof-statement consistency checker"
**Related learning:** docs/learning/2026-04-07-focused-prompt-beats-whole-paper.md

## Problem

The pipeline currently checks computational claims (SymPy) and notation consistency (cross-checker), but has no agent that asks: "does this proof actually establish what the theorem claims?" This is the root cause of the last missed Refine.ink finding — Proposition 1 claims rho->1 but the proof only shows rho^2->1, and no agent caught it because none asked the right question.

## Design

**Input:** A list of (theorem/proposition statement, proof) pairs extracted from the paper.

**Output:** For each pair, a verdict: does the proof's conclusion exactly match the statement's claim? If not, describe the gap (signs, directions, quantifiers, boundary cases).

**Pipeline position:** Math lane, after `math_extraction.py` extracts theorem/proof blocks. Runs in parallel with deterministic checks and other LLM review.

```
math_extraction.py  -->  proof blueprints  -->  proof-statement-checker (new)
                                           -->  math_deterministic.py (existing)
                                           -->  math_llm_review.py (existing)
```

**Module interactions:**
- `math_extraction.py`: already extracts theorem/proof blocks via `_build_proof_blueprints()`
- `math_review.py`: orchestrator — will dispatch to this checker alongside existing sub-modules
- `.claude/agents/`: needs a new agent definition file for static system instructions

**Model selection:** Reasoning-strong model (opus or gpt-5). Small context — only the statement+proof pair, not the full paper. The learning file confirmed that a focused 1,814-byte prompt found the issue immediately.

**Prompt pattern:**
```
For each (proposition/theorem statement, proof) pair:
  1. Extract the precise conclusion of the proof
  2. Extract the precise claim of the statement
  3. Compare: signs, directions, quantifiers, boundary cases
  4. Ask: could the proof's conclusion be weaker than claimed?
```

No SymPy or tool use needed — pure reasoning suffices.

## Implementation Plan

1. Create `.claude/agents/proof-statement-checker.md` — static system instructions for the agent
2. Add a `check_proof_statement_consistency()` function in `math_llm_review.py` (or a new `math_proof_statement.py` if it grows large)
3. Build a dynamic task prompt that injects each (statement, proof) pair
4. Wire into `math_review.py` orchestrator — run in parallel with existing proof review
5. Merge findings into the math report via `math_artifacts.py`

## Acceptance Criteria

- Run `revisica benchmark-refine --reviewer-a claude --use-llm-judge --llm-judge claude:sonnet --timeout-seconds 600` on targeting-interventions
- The rho->1 vs rho^2->1 gap in Proposition 1 must be flagged
- Recall should reach 100% (6/6) on targeting-interventions
- No regression on other benchmark cases

## Open Questions

- Should this checker also handle lemma/corollary pairs, or just theorem/proposition?
- Should it run on all proof blueprints, or only those not already covered by the existing proof reviewer?
- How to handle papers where proofs reference other results (proof by combining Lemma 2 + Lemma 3)?
