# Revisica vs Refine.ink Benchmark

- Manifest: `/Users/zichaoyang/workplace/Revisica/benchmarks/refine_cases/manifest.json`
- Report dir: `/Users/zichaoyang/workplace/Revisica/benchmarks/refine_cases/runs/refine-20260406-235109`
- Cases: 4
- **Aggregate recall (matched + partial):** 44.2%
- **Aggregate full recall (matched only):** 13.5%

## Per-Case Results

| Case | Expected | Found | Recall | Full Recall |
|------|----------|-------|--------|-------------|
| inference-molecular | 15 | 29 | 46.7% | 6.7% |
| coset-codes | 19 | 44 | 63.2% | 21.1% |
| targeting-interventions | 6 | 47 | 66.7% | 33.3% |
| chaotic-balanced-state | 12 | 0 | 0.0% | 0.0% |

## Detailed Match Breakdown

### inference-molecular
- Matched: 1, Partial: 6, Missed: 8
  - [X] Ambiguity in the stopping rule of Algorithm 1 (conf=0.00)
  - [~] Inconsistent notation for the sample type space (conf=0.27)
  - [X] Unproven normalization constant in Theorem 1 (conf=0.00)
  - [~] Possible notational inconsistency in proof of Theorem 1 (conf=0.44)
  - [+] Interpretation of the transition matrix in Proposition 1(e) (conf=0.47)
  - [~] Unclear step in the proof of Proposition 2 (conf=0.26)
  - [X] Use of a further approximation for $\hat{\pi}$ in applications (conf=0.00)
  - [X] Inverted description of microsatellite boundary conditions (conf=0.00)
  - [~] Justification for the infinite sites proposal distribution (conf=0.31)
  - [X] Clarity of the rooted tree sampler modification (Sec 5.5) (conf=0.00)
  - [X] Unclear description of ascertainment correction (conf=0.00)
  - [X] Proposed extension for long sequences is unclear (conf=0.00)
  - [X] Formulation of the Griffiths-Tavaré estimator (conf=0.00)
  - [~] Ambiguous notation in discussion of methods (conf=0.34)
  - [~] Incorrect recursive weight formula in SIS discussion (conf=0.44)

### coset-codes
- Matched: 4, Partial: 8, Missed: 7
  - [~] Decoding complexity as a geometric parameter (conf=0.36)
  - [X] Definition of fundamental volume and redundancy in the Introduction (conf=0.00)
  - [~] Role of algebraic structure in the coset code framework (conf=0.45)
  - [X] Mismatch in coset decomposition formulas (conf=0.00)
  - [X] Description of coset representatives in Sec. II.F (conf=0.00)
  - [~] Clarity of argument for mod-4 lattice structure (conf=0.28)
  - [+] Undefined notation for the dual of a Barnes-Wall lattice (conf=0.75)
  - [+] Notation for a lattice in Table III (conf=0.70)
  - [X] Description of the Ungerboeck encoder in Sec. IV.A (conf=0.00)
  - [+] Incorrect formula for lattice coding gain (conf=0.59)
  - [~] Incomplete premise in Lemma 6 (conf=0.27)
  - [~] Inconsistency in Decoding Complexity Calculation (conf=0.36)
  - [X] Unclear reference to "last three codes" (conf=0.00)
  - [~] Inconsistent encoder description for Class II codes (conf=0.39)
  - [~] Path enumeration for Class V error coefficient (conf=0.27)
  - [+] Minimum distance argument for Class VI codes (conf=0.53)
  - [X] Parameter mismatch for lattice X_32 in Discussion (conf=0.00)
  - [X] Incorrect example for γ=3 codes in Discussion (conf=0.00)
  - [~] Parameter comparison between Wei code and X24 lattice (conf=0.30)

### targeting-interventions
- Matched: 2, Partial: 2, Missed: 2
  - [X] Comparative static claim in Footnote 16 (conf=0.00)
  - [~] Limiting direction of intervention in Proposition 1 (conf=0.27)
  - [X] Sign error in discussion of Proposition 2 (substitutes case) (conf=0.00)
  - [~] "Maximizer" vs. "minimizer" for smallest eigenvalues (conf=0.30)
  - [+] Typo in Lagrangian in proof of Theorem 1 (conf=0.57)
  - [+] Unclear notation in proof of Proposition 2 (conf=0.50)

### chaotic-balanced-state
- Matched: 0, Partial: 0, Missed: 12
  - [X] Clarity of the model's scaling argument in the Introduction (conf=0.00)
  - [X] Clarification on the mean-field theory's regime of validity (conf=0.00)
  - [X] Inconsistent definition of connection probability in Sec. 2 (conf=0.00)
  - [X] Sign convention for quenched noise in Sec 5 (conf=0.00)
  - [X] Variance of inhibitory input in Sec 5.3 (conf=0.00)
  - [X] Discrepancy regarding stability boundaries in Sec. 6.2 (conf=0.00)
  - [X] Incorrect variance term in q_k expression (sec:Inhomogeneous Thresholds) (conf=0.00)
  - [X] Unclear derivation of q_k for bounded thresholds (conf=0.00)
  - [X] Inconsistent general formula for the rate distribution (conf=0.00)
  - [X] Prefactor in the distance dynamics equation (sec:8) (conf=0.00)
  - [X] Apparent contradiction on fast response to stimuli in Sec. 10.3 (conf=0.00)
  - [X] Standard deviation of input counts in Appendix A.1 (conf=0.00)

