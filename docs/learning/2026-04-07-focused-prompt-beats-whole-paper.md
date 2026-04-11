# Learning: Focused Prompt Beats Whole-Paper Review

**Date:** 2026-04-07
**Commit:** `3e13bc8`
**Context:** Refine.ink benchmark on targeting-interventions (Galeotti, Golub, Goyal)

## The Observation

Our pipeline ran ~68 parallel LLM calls on a 770-line economics paper and produced 100 findings. It caught 5 out of 6 Refine.ink issues. The last one — "Proposition 1 claims ρ→1 but the proof only shows ρ²→1" — was missed by every agent.

Then we fed Codex gpt-5.4 a **single focused prompt** (1,814 bytes) containing just the proposition statement + its proof, with the question "does this proof establish what the statement claims?" It found the issue immediately, with a detailed explanation of why squaring loses sign information.

## The Lesson

**The bottleneck is not model capability — it's prompt construction.**

| Approach | Saw the issue? | Why |
|----------|---------------|-----|
| whole-paper claim-verifier (opus) | No | 770 lines of context, claim buried in proof details |
| 48 per-claim SymPy tasks (opus) | No | Extracted the right claim, but asked "is this claim correct?" not "does the proof match the claim?" |
| **focused (statement, proof) pair** (gpt-5.4) | **Yes** | Small context, precise question, right framing |

The critical difference is not which model you use or how much compute you spend. It's **what question you ask** and **how much irrelevant context you strip away**.

## Architecture Implications

### 1. Three types of verification require three different prompt patterns

| Verification type | Prompt pattern | Example |
|-------------------|---------------|---------|
| **Computational claim** | "Here is a claim. Write SymPy to check it." | Footnote 16: is x_ℓ/x_{ℓ+1} increasing in β? |
| **Notation/formula consistency** | "Compare formula A at location X with formula B at location Y." | Lagrangian missing b̂² exponent |
| **Proof-statement gap** | "Here is statement S. Here is proof P. Does P establish exactly S?" | ρ→1 vs ρ²→1 |

Our current pipeline handles types 1 and 2. It misses type 3 because no agent asks the right question.

### 2. The proof-statement checker should be a separate agent

Not a tweak to existing agents, but a new role with a distinct prompt pattern:

```
For each (proposition/theorem statement, proof) pair:
  - Extract the precise conclusion of the proof
  - Extract the precise claim of the statement
  - Compare: signs, directions, quantifiers, boundary cases
  - Ask: could the proof's conclusion be weaker than claimed?
```

This agent doesn't need SymPy or Bash — pure reasoning suffices (Codex gpt-5.4 found it without any tool use). It needs a reasoning-strong model (opus or gpt-5.4) but small context.

### 3. Claim extraction must be paired with proof extraction

Current `extract_claims()` identifies **what is claimed** but not **what is proved**. To enable proof-statement gap detection, we need to:

1. Extract each proposition/theorem statement
2. Find its corresponding proof block
3. Pair them and send as a unit to the checker

The math_review.py `_build_proof_blueprints()` already does step 1-2 for LaTeX `\begin{theorem}...\end{proof}` blocks. We need the same for markdown papers where theorems appear as inline text.

### 4. The general principle: decompose by question type, not by paper section

Refine.ink's power doesn't come from looking at more sections — it comes from asking more types of questions. Our section combiner asks "are these sections consistent?" Our claim verifier asks "is this claim computationally correct?" But nobody asks "does this proof actually establish what it says it does?"

**Each distinct question type needs its own agent with a tailored prompt pattern.** The taxonomy of mathematical review questions is roughly:

1. Is this formula/symbol consistent across locations? → notation-tracker, formula-cross-checker
2. Is this computational claim correct? → claim-verifier (SymPy)
3. Does this proof establish what the theorem claims? → **proof-statement checker (new)**
4. Is this algorithm description unambiguous? → algorithm reviewer (future)
5. Are the assumptions sufficient for the conclusion? → assumption auditor (future)

### 5. Smaller context + precise question > larger context + vague question

This is the core Refine.ink insight, and our benchmark confirms it quantitatively:

- 100 findings from 68 calls with mixed context → missed the subtlest issue
- 1 finding from 1 call with 1,814 bytes of focused context → found it immediately

**When designing new agents, optimize for question precision first, context volume second.**
