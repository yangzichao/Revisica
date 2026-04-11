# ReviseAgent vs Refine.ink Benchmark

- Manifest: `/Users/zichaoyang/workplace/ReviseAgent/benchmarks/refine_cases/manifest_mini.json`
- Report dir: `/Users/zichaoyang/workplace/ReviseAgent/benchmarks/refine_cases/runs/refine-20260406-233518`
- Cases: 1
- **Aggregate recall (matched + partial):** 100.0%
- **Aggregate full recall (matched only):** 66.7%

## Per-Case Results

| Case | Expected | Found | Recall | Full Recall |
|------|----------|-------|--------|-------------|
| targeting-interventions | 6 | 56 | 100.0% | 66.7% |

## Detailed Match Breakdown

### targeting-interventions
- Matched: 4, Partial: 2, Missed: 0
  - [~] Comparative static claim in Footnote 16 (conf=0.33)
  - [~] Limiting direction of intervention in Proposition 1 (conf=0.38)
  - [+] Sign error in discussion of Proposition 2 (substitutes case) (conf=0.55)
  - [+] "Maximizer" vs. "minimizer" for smallest eigenvalues (conf=0.46)
  - [+] Typo in Lagrangian in proof of Theorem 1 (conf=0.54)
  - [+] Unclear notation in proof of Proposition 2 (conf=0.56)

