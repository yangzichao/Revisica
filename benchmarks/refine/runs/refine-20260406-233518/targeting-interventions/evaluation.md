# Refine Benchmark: targeting-interventions

- Paper: `/Users/zichaoyang/workplace/ReviseAgent/benchmarks/refine_cases/targeting-interventions.md`
- Expected comments: 6
- Our findings: 56
- Recall (matched + partial): 100.0%
- Full recall (matched only): 66.7%

## Expected vs Found

### [~] PARTIAL: Comparative static claim in Footnote 16

- **Refine score:** 0.8
- **Match confidence:** 0.33
- **Explanation:** Heuristic score: 0.33
- **Expected quote:** It can be verified that, for every $\ell \in\{1, \ldots, n-1\}$, the ratio $x_{\ell} / x_{\ell+1}$ is increasing (decreasing) in $\beta$ for the case of strategic complements (substitutes): thus the i...
- **Matched findings (1):**
  - [structure] Intuitive claim about eigenvector centrality and 'global contributions' lacks formal anchor

### [~] PARTIAL: Limiting direction of intervention in Proposition 1

- **Refine score:** 1.0
- **Match confidence:** 0.38
- **Explanation:** Heuristic score: 0.38
- **Expected quote:** If $\beta>0$ (the game features strategic complements), then the similarity of $\boldsymbol{y}^{*}$ and the first principal component of the network tends to $1: \rho\left(\boldsymbol{y}^{*}, \boldsym...
- **Matched findings (3):**
  - [basic] Sign mismatch in discussion of Proposition 2 bound for strategic substitutes
  - [basic] Misspelling 'faciliates' for 'facilitates'
  - [notation-tracker] Δb* used in proof of Proposition 2 without definition

### [+] MATCHED: Sign error in discussion of Proposition 2 (substitutes case)

- **Refine score:** 0.8
- **Match confidence:** 0.55
- **Explanation:** Heuristic score: 0.55
- **Expected quote:** If the game has the strategic substitutes property, $\beta<0$, then for any $\epsilon>0$, if $C> \frac{2\|\hat{\boldsymbol{b}}\|^{2}}{\epsilon}\left(\frac{\alpha_{n-1}}{\alpha_{n}-\alpha_{n-1}}\right)...
- **Matched findings (3):**
  - [basic] Sign mismatch in discussion of Proposition 2 bound for strategic substitutes
  - [notation-tracker] Denominator sign flipped in discussion of bottom gap under strategic substitutes
  - [formula-cross-checker] Denominator subscripts swapped in discussion of Proposition 2 for strategic substitutes

### [+] MATCHED: "Maximizer" vs. "minimizer" for smallest eigenvalues

- **Refine score:** 0.4
- **Match confidence:** 0.46
- **Explanation:** Heuristic score: 0.46
- **Expected quote:** Turning next to strategic substitutes, recall that the smallest two eigenvalues, $\lambda_{n}$ and $\lambda_{n-1}$, can be written as follows:
$$
\lambda_{n}=\min _{\boldsymbol{u}:\|\boldsymbol{u}\|=1...
- **Matched findings (3):**
  - [notation-tracker] Minimizers incorrectly called 'maximizers' for λ_n and λ_{n-1}
  - [formula-cross-checker] Bottom eigenvectors called 'maximizer' of minimization problems
  - [formula-cross-checker] Denominator subscripts swapped in discussion of Proposition 2 for strategic substitutes

### [+] MATCHED: Typo in Lagrangian in proof of Theorem 1

- **Refine score:** 0.4
- **Match confidence:** 0.54
- **Explanation:** Heuristic score: 0.54
- **Expected quote:** Observe that the Lagrangian corresponding to the maximization problem is

$$
\mathcal{L}=w \sum_{\ell=1}^{n} \alpha_{\ell}\left(1+x_{\ell}\right)^{2} \underline{\hat{b}}_{\ell}+\mu\left[C-\sum_{\ell=1...
- **Matched findings (3):**
  - [notation-tracker] Lagrangian missing exponent: b̂_ℓ instead of b̂_ℓ²
  - [notation-tracker] Δb* used in proof of Proposition 2 without definition
  - [notation-tracker] Underline missing on b̂_ℓ in Theorem 1's equation (6)

### [+] MATCHED: Unclear notation in proof of Proposition 2

- **Refine score:** 0.8
- **Match confidence:** 0.56
- **Explanation:** Heuristic score: 0.56
- **Expected quote:** Cosine similarity. We now turn to the cosine similarity result. We focus on the case of strategic complements. The proof for the case of strategic substitutes is analogous. We start by writing a usefu...
- **Matched findings (3):**
  - [basic] Cosine similarity definition omits ‖z‖ from denominator
  - [notation-tracker] Δb* used in proof of Proposition 2 without definition
  - [notation-tracker] Underline missing on b̂_ℓ in Theorem 1's equation (6)

