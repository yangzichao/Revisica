# Refine Benchmark: targeting-interventions

- Paper: `/Users/zichaoyang/workplace/ReviseAgent/benchmarks/refine_cases/targeting-interventions.md`
- Expected comments: 6
- Our findings: 47
- Recall (matched + partial): 66.7%
- Full recall (matched only): 33.3%

## Expected vs Found

### [X] MISSED: Comparative static claim in Footnote 16

- **Refine score:** 0.8
- **Match confidence:** 0.00
- **Explanation:** Heuristic score: 0.00
- **Expected quote:** It can be verified that, for every $\ell \in\{1, \ldots, n-1\}$, the ratio $x_{\ell} / x_{\ell+1}$ is increasing (decreasing) in $\beta$ for the case of strategic complements (substitutes): thus the i...

### [~] PARTIAL: Limiting direction of intervention in Proposition 1

- **Refine score:** 1.0
- **Match confidence:** 0.27
- **Explanation:** Heuristic score: 0.27
- **Expected quote:** If $\beta>0$ (the game features strategic complements), then the similarity of $\boldsymbol{y}^{*}$ and the first principal component of the network tends to $1: \rho\left(\boldsymbol{y}^{*}, \boldsym...
- **Matched findings (1):**
  - [basic] Misspelling: "faciliates" → "facilitates"

### [X] MISSED: Sign error in discussion of Proposition 2 (substitutes case)

- **Refine score:** 0.8
- **Match confidence:** 0.00
- **Explanation:** Heuristic score: 0.00
- **Expected quote:** If the game has the strategic substitutes property, $\beta<0$, then for any $\epsilon>0$, if $C> \frac{2\|\hat{\boldsymbol{b}}\|^{2}}{\epsilon}\left(\frac{\alpha_{n-1}}{\alpha_{n}-\alpha_{n-1}}\right)...

### [~] PARTIAL: "Maximizer" vs. "minimizer" for smallest eigenvalues

- **Refine score:** 0.4
- **Match confidence:** 0.30
- **Explanation:** Heuristic score: 0.30
- **Expected quote:** Turning next to strategic substitutes, recall that the smallest two eigenvalues, $\lambda_{n}$ and $\lambda_{n-1}$, can be written as follows:
$$
\lambda_{n}=\min _{\boldsymbol{u}:\|\boldsymbol{u}\|=1...
- **Matched findings (1):**
  - [notation-tracker] Eigenvectors u^n, u^{n-1} called 'maximizers' of minimization problems

### [+] MATCHED: Typo in Lagrangian in proof of Theorem 1

- **Refine score:** 0.4
- **Match confidence:** 0.57
- **Explanation:** Heuristic score: 0.57
- **Expected quote:** Observe that the Lagrangian corresponding to the maximization problem is

$$
\mathcal{L}=w \sum_{\ell=1}^{n} \alpha_{\ell}\left(1+x_{\ell}\right)^{2} \underline{\hat{b}}_{\ell}+\mu\left[C-\sum_{\ell=1...
- **Matched findings (3):**
  - [venue] Theorem-proof format without intuitive scaffolding is misaligned with general-academic expectations
  - [basic] Missing exponent $^2$ on $\underline{\hat{b}}_\ell$ in the Lagrangian
  - [notation-tracker] Underline notation inconsistently dropped on b̂_ℓ in principal-component basis

### [+] MATCHED: Unclear notation in proof of Proposition 2

- **Refine score:** 0.8
- **Match confidence:** 0.50
- **Explanation:** Heuristic score: 0.50
- **Expected quote:** Cosine similarity. We now turn to the cosine similarity result. We focus on the case of strategic complements. The proof for the case of strategic substitutes is analogous. We start by writing a usefu...
- **Matched findings (2):**
  - [notation-tracker] Spurious asterisk on α₂ in proof of Proposition 2
  - [notation-tracker] New symbol Δb* introduced without definition in proof of Proposition 2

