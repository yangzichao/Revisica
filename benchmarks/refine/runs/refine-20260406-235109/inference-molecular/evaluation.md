# Refine Benchmark: inference-molecular

- Paper: `/Users/zichaoyang/workplace/Revisica/benchmarks/refine_cases/inference-molecular.md`
- Expected comments: 15
- Our findings: 29
- Recall (matched + partial): 46.7%
- Full recall (matched only): 6.7%

## Expected vs Found

### [X] MISSED: Ambiguity in the stopping rule of Algorithm 1

- **Refine score:** 0.18
- **Match confidence:** 0.00
- **Explanation:** Heuristic score: 0.00
- **Expected quote:** Step 3: if there are fewer than n+1 lines in the ancestry return to step 2 . Otherwise go back to the last time at which there were n lines in the ancestry and stop....

### [~] PARTIAL: Inconsistent notation for the sample type space

- **Refine score:** 0.18
- **Match confidence:** 0.27
- **Explanation:** Heuristic score: 0.27
- **Expected quote:** The history $\mathcal{H}$ thus includes a record of the states $\left(H_{-m}, H_{-(m-1)}, \ldots, H_{1}, H_{0}\right)$ visited by a Markov process beginning with the genetic type $H_{-m} \in E$ of the...
- **Matched findings (1):**
  - [structure] Abstract claim of 'several orders of magnitude' efficiency gain is not uniformly supported by empirical evidence

### [X] MISSED: Unproven normalization constant in Theorem 1

- **Refine score:** 0.18
- **Match confidence:** 0.00
- **Explanation:** Heuristic score: 0.00
- **Expected quote:** The constant of proportionality $C$ is given by

$$
C=\frac{n(n-1+\theta)}{2},
$$

where $n$ is the number of chromosomes in $H_{i}$.
Proof. That $Q_{\theta}^{*}$ is in the class $\mathcal{M}$ follows...

### [~] PARTIAL: Possible notational inconsistency in proof of Theorem 1

- **Refine score:** 0.09
- **Match confidence:** 0.44
- **Explanation:** Heuristic score: 0.44
- **Expected quote:** P\left\{\Upsilon_{\mathrm{m}} \cap A_{k}(t-\delta)=\left(\alpha_{1}, \ldots, \alpha_{k-1}, \beta\right) \mid A_{k}(t)=\left(\alpha_{1}, \ldots, \alpha_{k-1}, \alpha\right)\right\} & \\
\quad= & \frac{...
- **Matched findings (3):**
  - [basic] Subscript '$n-1$' should be '$k-1$' in backward-rate derivation
  - [notation-tracker] Index switches from k to n in Theorem 1 proof (mutation backward rate)
  - [notation-tracker] Missing fraction bar in coalescence backward-rate derivation

### [+] MATCHED: Interpretation of the transition matrix in Proposition 1(e)

- **Refine score:** 0.55
- **Match confidence:** 0.47
- **Explanation:** Heuristic score: 0.47
- **Expected quote:** The distribution $\hat{\pi}\left(\cdot \mid A_{n}\right)$ is the stationary distribution of the Markov chain on $E$ with transition matrix

$$
T_{\beta \alpha}=\frac{\theta}{n+\theta} P_{\beta \alpha}...
- **Matched findings (1):**
  - [basic] Remark 1 refers to '$\pi$' where '$\hat{\pi}$' is intended

### [~] PARTIAL: Unclear step in the proof of Proposition 2

- **Refine score:** 0.09
- **Match confidence:** 0.26
- **Explanation:** Heuristic score: 0.26
- **Expected quote:** Thus

$$
\begin{aligned}
\frac{n_{\alpha}}{n} & =\sum_{\beta \in E} \frac{\hat{\pi}\left(\beta \mid H_{i}-\alpha\right)}{\hat{\pi}\left(\alpha \mid H_{i}-\alpha\right)}\left(\frac{\theta}{n-1+\theta} ...
- **Matched findings (1):**
  - [basic] Subscript '$n-1$' should be '$k-1$' in backward-rate derivation

### [X] MISSED: Use of a further approximation for $\hat{\pi}$ in applications

- **Refine score:** 0.09
- **Match confidence:** 0.00
- **Explanation:** Heuristic score: 0.00
- **Expected quote:** Note that this model has $2^{10}$ different alleles, and so the calculation of the quantities $\hat{\pi}\left(\beta \mid A_{n}\right)$ using equations (18) and (19) appears to be computationally daunt...

### [X] MISSED: Inverted description of microsatellite boundary conditions

- **Refine score:** 0.36
- **Match confidence:** 0.00
- **Explanation:** Heuristic score: 0.00
- **Expected quote:** The implementation of our IS scheme is facilitated by centring the sample distribution near 10 repeats and truncating the type space $E$ to $\{0,1, \ldots, 19\}$ by insisting that all mutations to all...

### [~] PARTIAL: Justification for the infinite sites proposal distribution

- **Refine score:** 0.45
- **Match confidence:** 0.31
- **Explanation:** Heuristic score: 0.31
- **Expected quote:** These problems are not insurmountable, but for simplicity we adapt our earlier approach to this context by analogy with proposition 2: recall that one method of simulating from our IS function $Q^{\ma...
- **Matched findings (3):**
  - [structure] Abstract claim of 'several orders of magnitude' efficiency gain is not uniformly supported by empirical evidence
  - [structure] Abstract conflates the theoretical characterization (Theorem 1) and the algorithmic contribution (SD scheme) without prioritizing either
  - [structure] Section 3.4 introduces IS without a transition from the preceding MCMC discussion

### [X] MISSED: Clarity of the rooted tree sampler modification (Sec 5.5)

- **Refine score:** 0.09
- **Match confidence:** 0.00
- **Explanation:** Heuristic score: 0.00
- **Expected quote:** To facilitate a comparison with published estimates, we modified our IS function to analyse rooted trees, by adding to conditions (a) and (b) above a condition that no mutation can occur backwards in ...

### [X] MISSED: Unclear description of ascertainment correction

- **Refine score:** 0.73
- **Match confidence:** 0.00
- **Explanation:** Heuristic score: 0.00
- **Expected quote:** For the IS schemes that we have considered, assuming the infinite sites mutation model, the ascertainment effect can be accommodated by labelling every lineage which leads to any chromosome in the pan...

### [X] MISSED: Proposed extension for long sequences is unclear

- **Refine score:** 0.73
- **Match confidence:** 0.00
- **Explanation:** Heuristic score: 0.00
- **Expected quote:** The effect of the non-varying sites could then be taken into account by the factor $\pi_{\theta}\left(A_{n} \mid \mathcal{H}^{(i)}\right)$ in estimator (9), which could be calculated by the peeling al...

### [X] MISSED: Formulation of the Griffiths-Tavaré estimator

- **Refine score:** 0.45
- **Match confidence:** 0.00
- **Explanation:** Heuristic score: 0.00
- **Expected quote:** In the Griffiths-Tavaré method, view the problem of finding $\{p(\mathbf{n})\}$ as solving the system of linear
equations (34). Importance sampling techniques were used to obtain a solution of the equ...

### [~] PARTIAL: Ambiguous notation in discussion of methods

- **Refine score:** 0.18
- **Match confidence:** 0.34
- **Explanation:** Heuristic score: 0.34
- **Expected quote:** In the Stephens-Donnelly method,

$$
p\left(H_{j}\right)=\sum \frac{p\left(H_{j} \mid H_{j-1}^{\prime}\right)}{\hat{p}\left(H_{j-1}^{\prime} \mid H_{j}\right)} \hat{p}\left(H_{j-1}^{\prime} \mid H_{j}...
- **Matched findings (2):**
  - [venue] Verbatim discussant comments and ceremonial 'vote of thanks' embedded in the manuscript body
  - [notation-tracker] $w_\theta$ drifts to $\omega_\theta$ in Ventura's discussion

### [~] PARTIAL: Incorrect recursive weight formula in SIS discussion

- **Refine score:** 0.36
- **Match confidence:** 0.44
- **Explanation:** Heuristic score: 0.44
- **Expected quote:** As with many SIS applications, both Stephens and Donnelly, and Griffiths and Tavaré (1994) propose trial densities $q_{0}(\mathcal{H})$ of the form

$$
q_{\theta}(\mathcal{H})=\prod_{i=0}^{-(m-1)} q_{...
- **Matched findings (3):**
  - [notation-tracker] Wrong subscript in Chen & Liu weight recursion: $H_{-1}$ should be $H_{-t}$
  - [notation-tracker] $w_\theta$ drifts to $\omega_\theta$ in Ventura's discussion
  - [formula-cross-checker] Chen–Liu discussion: recursive weight has H_{-1} instead of H_{-t}

