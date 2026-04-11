# ReviseAgent — TODO

## Next: Close the recall gap against Refine.ink

**Goal:** 100% recall — everything Refine.ink finds, we must also find.

**Current status (2026-04-07):** 83.3% recall on targeting-interventions (5/6, LLM judge). See `benchmarks/refine_cases/runs/` and `docs/benchmark-reports/` for detailed reports.

### High Priority

- [ ] **Proof-statement consistency checker** — The last missed finding (ρ→1 vs ρ²→1 in Proposition 1) requires comparing what a theorem *states* with what its proof actually *establishes*. Specifically: does the proof show ρ→1 or only |ρ|→1? This is a "proof proves less than claimed" gap, not a computational claim. Needs a dedicated agent that takes each (proposition statement, proof) pair and checks whether the proof's conclusion exactly matches the statement, including signs, directions, and quantifiers.

- [ ] **Re-run full benchmark with LLM judge** on all 4 cases (chaotic-balanced-state hit rate limit last time) to establish accurate cross-paper recall.

### Medium Priority

- [ ] **Algorithm reviewer agent** — Dedicated agent for analyzing pseudocode/algorithm blocks for ambiguity, off-by-one errors, and unclear stopping conditions.

- [ ] **Increase section combination budget** — Currently capped at 30 combos. For longer papers (coset-codes has 33 sections), increase or make adaptive.

- [ ] **Cross-provider benchmark** — Run refine benchmark with both `--reviewer-a claude --reviewer-b codex` to test cross-check quality.

### Completed (2026-04-07)

- [x] Massive parallelism — all roles, section combos, self-checks run concurrently (ThreadPoolExecutor, 10-12 workers)
- [x] Section combination generator — `section_combiner.py` with LaTeX + Markdown heading support
- [x] Writing self-check layer — filters false positives between role execution and judge
- [x] Task-model auto-routing — `model_router.py` routes math→opus/o3, writing→sonnet/gpt-4.1
- [x] Refine.ink benchmark runner — `benchmark_refine.py` with heuristic + LLM judge matching
- [x] `benchmark-refine` CLI command
- [x] Claim-by-claim verifier — `claim_extractor.py` extracts per-paragraph/footnote claims, each verified as independent parallel SymPy task. Recovered Footnote 16 comparative static (previously missed). Recall: 67% → 83%.

## Running the benchmark

```bash
# Quick test (1 case, heuristic matching)
revise-agent benchmark-refine --manifest benchmarks/refine_cases/manifest_mini.json --reviewer-a claude

# Full run with LLM judge for accurate recall
revise-agent benchmark-refine --reviewer-a claude --use-llm-judge --llm-judge claude:sonnet --timeout-seconds 600

# Dual provider
revise-agent benchmark-refine --reviewer-a claude --reviewer-b codex --timeout-seconds 600
```
