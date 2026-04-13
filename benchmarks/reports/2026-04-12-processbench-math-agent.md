# ProcessBench Math Agent Benchmark Report

**Date:** 2026-04-12
**Commit:** 92a7d47 (base) + uncommitted changes (agent versioning, parsing fix, retry logic, v0-v4 prompts)
**Suite:** ProcessBench (Qwen/ProcessBench), split=math, 50 cases
**Metric:** exact_first_error_accuracy — does the agent correctly identify the first erroneous step?

## Summary

| Model | v0 (baseline) | v3 (structured + tools) | v4 (+ self-check) |
|---|---|---|---|
| **Opus** | 56% | **58%** | 52% (-6%) |
| **Sonnet** | — | 56% | **58%** (+2%) |
| **Haiku** | — | 48% | 46% (-2%) |
| **Codex (GPT-5)** | — | 26%* | — |

Best result: **v3/Opus = v4/Sonnet = 58%** (29/50).

*Codex ran 41/50 cases with schema+sandbox fix. Accuracy is 11/41. Codex consistently over-reports Step 0 (same pattern as early Claude v0). Codex is deprioritized for math agent benchmarks until further investigation.

## Prompt Versions

| Version | Key Changes | Tools |
|---|---|---|
| v0 | Minimal: "read file, assess obligations, return JSON" | Read, Glob, Grep |
| v1 | + chain-of-thought, + step-by-step methodology, + error patterns | + Bash, WebSearch, WebFetch |
| v2 | + "compute before judging", + "don't flag Step 0 unless proven wrong" | same as v1 |
| v3 | + mandatory Bash verification, + precise step referencing, + long-chain strategy | same as v1 |
| v4 | + two-pass self-check: find candidate error, re-verify with different computation before reporting | same as v1 |

## Key Findings

### 1. Parsing bug was the biggest single improvement

Initial v0 accuracy was **10%** due to a parsing bug: the framework treated LLM findings marked `status: "correct"` as issues, and `min()` over all issue step numbers always yielded Step 0. Fixing this raised v0 from 10% → **56%** — a 5.6x improvement from a one-line code fix.

A second parsing crash (`step_index: "additional"` from Haiku) was also fixed with safe int parsing.

### 2. Prompt optimization: v0 → v3 = +2% (not significant at n=50)

| Version | Accuracy (50 cases, Opus) |
|---|---|
| v0 | 56% |
| v1 | 50% (10 cases only) |
| v2 | 40% (regression, 10 cases) |
| v3 | **58%** |
| v4 | 52% (regression) |

The v0→v3 improvement (+2%) is within noise for 50 samples. Prompt engineering alone does not break through the ~58% ceiling.

### 3. Self-check (v4) hurts strong and weak models, helps mid-range

v4's "verify your candidate error with a second independent computation" strategy:
- **Opus: -6%** — the model was already right, self-check caused it to second-guess correct answers
- **Sonnet: +2%** — mild benefit, self-check caught a few false positives
- **Haiku: -2%** — model too weak to reliably self-check; adds noise

### 4. Model scaling matters more than prompt engineering

```
Haiku 48% → Sonnet 56% → Opus 58%
  (+8%)         (+2%)
```

The jump from Haiku to Sonnet is larger than any prompt change. Sonnet at v4 (58%) matches Opus at v3 (58%) — making Sonnet the best cost/accuracy tradeoff.

### 5. Failure mode analysis (v3/Opus, 50 cases)

Of 21 failures:
- **12 (57%) reported too early** — flagged a correct step before the actual error
- **7 (33%) reported too late** — missed the error and flagged a later step
- **2 (10%) no output** — timeout or unparseable response

"Reporting too early" (false positive on a correct step) is the dominant failure mode. This is a model reasoning precision issue, not solvable by prompt changes alone.

## Timing

| Model | Median per case | Total (50 cases) |
|---|---|---|
| Opus (v3) | ~65s | ~75 min |
| Sonnet (v3) | ~60s | ~77 min |
| Haiku (v3) | ~20s | ~21 min |

## Comparison to Published SOTA

| Method | ProcessBench Accuracy | Notes |
|---|---|---|
| **Our v3/Opus** | **58%** | Single agent, no training |
| **Our v4/Sonnet** | **58%** | Single agent + self-check |
| GPT-4o (published) | 61-69% | Varies by version |
| Temporal Consistency (K=5, DeepSeek-R1-7B) | 71% | Multi-agent iterative self-check |
| NCV decomposition (Qwen2.5-32B) | 69% | Atomic claim verification |
| o1-mini | 72-74% | Reasoning-specialized model |
| Qwen2.5-Math-PRM-72B | 73.5% | Trained PRM (not inference-only) |

Our 58% is consistent with single-agent prompted LLM performance. Published techniques to reach 70%+:
1. **Multi-agent voting** (Temporal Consistency): K=3-5 independent verifiers, iterative self-check, majority vote
2. **Atomic decomposition** (NCV): Break each step into yes/no sub-claims, verify separately
3. **Reasoning-specialized models**: o1-mini, DeepSeek-R1 achieve higher base accuracy

## Recommended Next Steps

1. **Multi-agent voting (v5)**: Run 3 independent verification passes, only flag a step if ≥2/3 agree. Predicted impact: +8-12%.
2. **NCV atomic decomposition (v6)**: For the candidate error step, extract atomic claims and verify each with a binary yes/no prompt. Predicted impact: +10-15%.
3. **Sonnet as default**: v4/Sonnet matches v3/Opus at lower cost. Use Sonnet for the math lane.
4. **Codex comparison**: Run same benchmarks with Codex/GPT to compare provider families.
5. **Scale to 200+ cases**: Current 50-case runs have high variance (~±7%). Need more samples for reliable comparison.

## Commands

```bash
# Reproduce
revisica benchmark-run --suite processbench --split math --limit 50 \
  --mode single-agent --reviewer claude --timeout-seconds 1200 \
  --agent-version v3 --output-dir benchmarks/runs/pb-v3-opus-50

# Compare versions
python3 scripts/analyze_processbench.py benchmarks/runs/pb-v3-50 benchmarks/runs/pb-v4-opus-50

# Full suite
bash scripts/run_benchmark_suite.sh
```

## Codex (GPT-5) Analysis

Codex achieved 26% accuracy (10/39 effective cases), significantly below Claude. Contributing factors:

1. **Usage limit**: Codex hit daily usage limit after ~39 cases, producing empty output for remaining 11. This is an account-level constraint, not a model issue.
2. **Output schema mismatch**: Codex uses `--output-schema findings.schema.json` which enforces `category/severity/title/snippet/explanation/fix/rewrite` fields but lacks `step_index`. Step extraction relies on fallback regex from `rewrite` field text — less reliable than Claude's direct `step_index` field.
3. **Sandbox limitation**: Codex sandbox is `read-only`, so Bash tool calls for SymPy verification (key to v3/v4 prompts) may not execute properly.
4. **Model difference**: GPT-5 via Codex CLI may have different math reasoning characteristics than Claude Opus/Sonnet.

**Status**: Schema and sandbox issues fixed (step_index added, workspace-write enabled). Re-run with fixes yielded 27% (11/41) — still far below Claude. The dominant failure mode is over-reporting Step 0 (63% of failures), same as Claude v0 before parsing fix. However, unlike Claude, Codex's `--output-schema` forces structured output without free-form reasoning, preventing chain-of-thought before JSON. **Codex is deprioritized for math agent benchmarks** — focus on Claude Sonnet (best cost/accuracy).

## Artifacts

| Run | Path |
|---|---|
| v0/Opus (50) | `benchmarks/runs/pb-v0-50/` |
| v3/Opus (50) | `benchmarks/runs/pb-v3-50/` |
| v4/Opus (50) | `benchmarks/runs/pb-v4-opus-20260412-092726/` |
| v3/Sonnet (50) | `benchmarks/runs/pb-v3-sonnet-20260412-092726/` |
| v4/Sonnet (50) | `benchmarks/runs/pb-v4-sonnet-20260412-092726/` |
| v3/Haiku (50) | `benchmarks/runs/pb-v3-haiku-20260412-092726/` |
| v4/Haiku (50) | `benchmarks/runs/pb-v4-haiku-50-rerun/` |
| v3/Codex (41 effective, schema fixed) | `benchmarks/runs/pb-v3-codex-fixed/` |
