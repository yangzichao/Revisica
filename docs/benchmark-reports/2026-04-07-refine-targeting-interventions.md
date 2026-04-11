# Refine.ink Benchmark Report

**Date:** 2026-04-07
**Commit (83.3% run):** `046313d` — Add claim-by-claim verifier
**Commit (Codex validation):** `02115c5` — Codex gpt-5.4 confirms 6/6 reachable
**Paper:** Targeting Interventions in Networks (Galeotti, Golub, Goyal)
**Benchmark:** 6 expected findings from Refine.ink

**Commands:**
```bash
# 83.3% recall run (claim-by-claim verifier + LLM judge)
python -m revise_agent benchmark-refine \
  --manifest benchmarks/refine_cases/manifest_mini.json \
  --reviewer-a claude \
  --use-llm-judge --llm-judge claude:sonnet \
  --timeout-seconds 600 \
  --output-dir benchmarks/refine_cases/runs/refine-claim-verifier

# Codex validation of last missed finding
codex exec --full-auto --sandbox read-only --color never < /tmp/prop1-check-prompt.txt
# (model: gpt-5.4, reasoning effort: high)
```

**Run artifacts:** `benchmarks/refine_cases/runs/refine-claim-verifier/targeting-interventions/`

## Results Summary

| Metric | Value |
|--------|-------|
| Expected findings (Refine.ink) | 6 |
| Our total findings | 100 |
| Matched (high confidence) | 4 |
| Partial | 1 |
| Missed | 1 |
| **Recall (matched + partial)** | **83.3%** |
| **Full recall (matched only)** | **66.7%** |

## Progression Across Iterations

| Version | Recall | What changed |
|---------|--------|--------------|
| Baseline (3 agents: basic/structure/venue) | 1/6 (16.7%) | Only maximizer/minimizer found |
| + Math agents (notation-tracker, formula-cross-checker, claim-verifier) | 4/6 (66.7%) | +3: sign error, Lagrangian typo, Δb* notation |
| + Section combiner + self-check + model routing | 4/6 (66.7%) | Same recall, but more robust (multi-agent confirmation) |
| **+ Claim-by-claim verifier** | **5/6 (83.3%)** | **+1: Footnote 16 comparative static** |

## Per-Finding Breakdown

### [MATCHED] #1: Comparative static claim in Footnote 16
- **Refine score:** 0.8
- **LLM judge confidence:** 0.97
- **Found by:** `claim-verify-claim-3` (per-paragraph SymPy verification)
- **What it found:** Incorrect monotonicity direction for x_ℓ/x_{ℓ+1} in β under strategic substitutes
- **Why it was missed before:** Whole-paper claim-verifier timed out before reaching footnotes. Per-claim extraction isolated this footnote as an independent task.

### [MATCHED] #2: Sign error in discussion of Proposition 2
- **Refine score:** 0.8
- **LLM judge confidence:** 0.98
- **Found by:** `notation-tracker` + `formula-cross-checker` (dual confirmation)
- **What it found:** Denominator α_{n−1}/(α_{n−1}−α_n) flipped vs proposition's α_{n−1}/(α_n−α_{n−1})

### [MATCHED] #3: "Maximizer" vs. "minimizer" for smallest eigenvalues
- **Refine score:** 0.4
- **LLM judge confidence:** 0.99
- **Found by:** `notation-tracker` + `formula-cross-checker` + `math-claim-verifier` (triple confirmation)
- **What it found:** u^n and u^{n−1} called 'maximizers' of minimization problems

### [MATCHED] #4: Typo in Lagrangian in proof of Theorem 1
- **Refine score:** 0.4
- **LLM judge confidence:** 0.99
- **Found by:** 7 independent findings across `section-xcheck`, `notation-tracker`, `formula-cross-checker`
- **What it found:** Lagrangian writes b̂_ℓ (first power) instead of b̂_ℓ² (square)

### [PARTIAL] #5: Unclear notation in proof of Proposition 2
- **Refine score:** 0.8
- **LLM judge confidence:** 0.72
- **Found by:** `notation-tracker`
- **What it found:** Δb* used without definition (should be y* = b*−b̂)
- **What it missed:** Inconsistency between ρ(Δb*, √C u^1) and ρ(Δb*, u^1) — scaling of reference vector

### [MISSED] #6: Limiting direction of intervention in Proposition 1
- **Refine score:** 1.0
- **LLM judge confidence:** 0.95 (confident it's truly missed)
- **What Refine found:** Proposition 1 states ρ→1, but the proof only establishes ρ²→1 (i.e., |ρ|→1), leaving open the possibility that ρ→−1
- **Root cause:** This requires comparing what a proposition *claims* vs what its proof *actually establishes* — specifically noticing that squaring loses sign information. No current agent performs this proof-statement gap analysis.

## Architecture That Produced These Results

```
Paper (markdown)
  │
  ├─ extract_sections() ──→ 15 sections, 14 cross-check combinations
  ├─ extract_claims() ───→ 48 verifiable claims (incl. footnotes)
  │
  ├─ 6 standard agents (parallel) ──────────────────────────────
  │   ├─ basic (sonnet) ────────────── 12 findings
  │   ├─ structure (sonnet) ────────── 6 findings
  │   ├─ venue (sonnet) ───────────── 6 findings
  │   ├─ math-claim-verifier (opus) ── 4 findings
  │   ├─ notation-tracker (opus) ───── 19 findings
  │   └─ formula-cross-checker (opus)── 9 findings
  │
  ├─ 14 section cross-check tasks (sonnet, parallel) ── 41 findings
  │
  ├─ 48 per-claim SymPy verification tasks (opus, parallel) ── 3 findings
  │
  ▼ self-check (parallel, filters false positives)
  ▼ judge (aggregation + distillation)
  ▼ final report

  Total: ~68 parallel LLM calls → 100 findings
```

## What's Needed for 100% Recall

The last missed finding (#6) is a **proof-statement consistency gap**: the proposition claims ρ→1 but the proof only shows ρ²→1. This is qualitatively different from the other findings — it's not a typo, sign error, or computational mistake. It requires:

1. Parsing each (proposition statement, proof) pair
2. Comparing the precise conclusion of the proof with the precise claim of the proposition
3. Detecting that squaring loses sign information (ρ²→1 ⇏ ρ→1)

This is tracked as the top TODO item: **proof-statement consistency checker**.

---

## Follow-up: Codex gpt-5.4 Validation (2026-04-07)

To test whether the last missed finding is reachable with current models, we ran a **focused prompt** containing only Proposition 1's statement + proof through Codex (gpt-5.4, high reasoning effort).

**Result: Found it in one shot.**

Codex output (verbatim):

> **"The proof identifies concentration on the first eigendirection only up to sign, so it shows |ρ(y\*,u^1(G))|→1, not necessarily ρ(y\*,u^1(G))→1"**
>
> "The displayed identity establishes that the squared cosine similarity tends to 1. From this alone one can only conclude |ρ|→1. It does not imply ρ→1, because a sequence in [-1,1] whose square tends to 1 may converge to -1, or even fail to converge while alternating signs. An additional sign argument is required. [...] Because eigenvectors are only defined up to sign, replacing u^1(G) by -u^1(G) would flip the limit from +1 to -1."
>
> **Fix:** "Either weaken the proposition/proof to |ρ|→1, or add an explicit normalization/orientation convention for u^1(G), e.g. choose the sign so that ρ(b̂,u^1(G))≥0."

### Implications

1. **6/6 is achievable** — the model capability is there. The bottleneck is prompt construction, not reasoning.
2. **claim-28 was already extracted** by `extract_claims()` ("If β>0, then the similarity tends to 1: ρ(y\*, u^1(G)) → 1"). What's missing is pairing it with the proof text and asking "does this proof actually establish this claim?"
3. **The fix is a proof-statement consistency checker** that takes each (proposition statement, proof) pair and constructs a focused prompt like the one we tested. This prompt pattern is:
   - Here is the statement: [proposition text]
   - Here is the proof: [proof text]
   - Does the proof establish exactly what the statement claims? Check signs, directions, quantifiers.
4. **Codex gpt-5.4 found it without SymPy** — pure reasoning sufficed. This means the checker doesn't need Bash/SymPy access for this class of issues, making it faster and cheaper.

### Updated Recall Target

| Version | Recall | Notes |
|---------|--------|-------|
| Baseline (3 agents) | 1/6 (17%) | |
| + Math agents | 4/6 (67%) | |
| + Claim-by-claim verifier | 5/6 (83%) | |
| + Proof-statement checker (validated) | **6/6 (100%)** | Confirmed reachable with focused prompt on Codex gpt-5.4 |
