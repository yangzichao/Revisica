# Revisica vs Refine.ink Benchmark

- Manifest: `/Users/zichaoyang/workplace/Revisica/benchmarks/refine_cases/manifest_mini.json`
- Report dir: `/Users/zichaoyang/workplace/Revisica/benchmarks/refine_cases/runs/refine-claim-verifier`
- Cases: 1
- **Aggregate recall (matched + partial):** 83.3%
- **Aggregate full recall (matched only):** 66.7%

## Per-Case Results

| Case | Expected | Found | Recall | Full Recall |
|------|----------|-------|--------|-------------|
| targeting-interventions | 6 | 100 | 83.3% | 66.7% |

## Detailed Match Breakdown

### targeting-interventions
- Matched: 4, Partial: 1, Missed: 1
  - [+] Comparative static claim in Footnote 16 (conf=0.97)
  - [X] Limiting direction of intervention in Proposition 1 (conf=0.95)
  - [+] Sign error in discussion of Proposition 2 (substitutes case) (conf=0.98)
  - [+] "Maximizer" vs. "minimizer" for smallest eigenvalues (conf=0.99)
  - [+] Typo in Lagrangian in proof of Theorem 1 (conf=0.99)
  - [~] Unclear notation in proof of Proposition 2 (conf=0.72)

