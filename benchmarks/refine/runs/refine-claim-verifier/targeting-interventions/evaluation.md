# Refine Benchmark: targeting-interventions

- Paper: `/Users/zichaoyang/workplace/ReviseAgent/benchmarks/refine_cases/targeting-interventions.md`
- Expected comments: 6
- Our findings: 100
- Recall (matched + partial): 83.3%
- Full recall (matched only): 66.7%

## Expected vs Found

### [+] MATCHED: Comparative static claim in Footnote 16

- **Refine score:** 0.8
- **Match confidence:** 0.97
- **Explanation:** LLM judge: Finding #94 directly identifies the incorrect monotonicity direction for x_ℓ/x_{ℓ+1} in β under strategic substitutes, quoting the same snippet from Footnote 16 and explaining that the ratio is actually increasing in β for all β (including β<0), contradicting the paper's 'decreasing' claim for substitutes.
- **Expected quote:** It can be verified that, for every $\ell \in\{1, \ldots, n-1\}$, the ratio $x_{\ell} / x_{\ell+1}$ is increasing (decreasing) in $\beta$ for the case of strategic complements (substitutes): thus the i...
- **Matched findings (1):**
  - [claim-verify-claim-3] Incorrect monotonicity direction for x_ℓ/x_{ℓ+1} in β under strategic substitutes

### [X] MISSED: Limiting direction of intervention in Proposition 1

- **Refine score:** 1.0
- **Match confidence:** 0.95
- **Explanation:** LLM judge: No actual finding addresses the mathematical subtlety that Proposition 1(2a–b) asserts ρ(y*, u^1) → 1 (convergence of cosine similarity itself) when the proof only establishes ρ²→1 (or |ρ|→1), because the sign of the cosine similarity could flip. This issue — distinguishing convergence of ρ from convergence of ρ² — is entirely absent from the 100 actual findings.
- **Expected quote:** If $\beta>0$ (the game features strategic complements), then the similarity of $\boldsymbol{y}^{*}$ and the first principal component of the network tends to $1: \rho\left(\boldsymbol{y}^{*}, \boldsym...

### [+] MATCHED: Sign error in discussion of Proposition 2 (substitutes case)

- **Refine score:** 0.8
- **Match confidence:** 0.98
- **Explanation:** LLM judge: Finding #52 and Finding #71 both identify that the discussion paragraph for the substitutes case of Proposition 2 writes α_{n−1}/(α_{n−1}−α_n) with a sign-flipped denominator relative to the proposition statement, which correctly uses α_{n−1}/(α_n−α_{n−1}). Both findings note the denominator is negative in the discussion but positive in the proposition, and that the ratio is squared in the bound.
- **Expected quote:** If the game has the strategic substitutes property, $\beta<0$, then for any $\epsilon>0$, if $C> \frac{2\|\hat{\boldsymbol{b}}\|^{2}}{\epsilon}\left(\frac{\alpha_{n-1}}{\alpha_{n}-\alpha_{n-1}}\right)...
- **Matched findings (2):**
  - [notation-tracker] Denominator order flipped: α_{n−1}/(α_{n−1}−α_n) vs α_{n−1}/(α_n−α_{n−1})
  - [formula-cross-checker] Discussion paragraph swaps denominator sign relative to Proposition 2

### [+] MATCHED: "Maximizer" vs. "minimizer" for smallest eigenvalues

- **Refine score:** 0.4
- **Match confidence:** 0.99
- **Explanation:** LLM judge: Findings #43, #68, and #86 all independently flag that u^n and u^{n−1} are called 'maximizers' of the Rayleigh–Ritz problems defining λ_n and λ_{n−1}, even though those problems are stated as minimizations (confirmed by the arg-min on line 324). Each finding notes this is a copy-paste slip from the complements paragraph, where u^1 and u^2 are correctly called maximizers.
- **Expected quote:** Turning next to strategic substitutes, recall that the smallest two eigenvalues, $\lambda_{n}$ and $\lambda_{n-1}$, can be written as follows:
$$
\lambda_{n}=\min _{\boldsymbol{u}:\|\boldsymbol{u}\|=1...
- **Matched findings (3):**
  - [notation-tracker] 'maximizer' should be 'minimizer' for λ_n and λ_{n−1}
  - [formula-cross-checker] Eigenvectors u^n, u^{n-1} called 'maximizers' of minimization problems
  - [math-claim-verifier] Section 4.2: u^n and u^(n-1) called 'maximizers' of minimization problems

### [+] MATCHED: Typo in Lagrangian in proof of Theorem 1

- **Refine score:** 0.4
- **Match confidence:** 0.99
- **Explanation:** LLM judge: Findings #38, #44, #69, #75, #85, #88, and #96 all identify the same error: the Lagrangian in the proof of Theorem 1 writes the objective term with b̂_ℓ (first power) instead of b̂_ℓ² (square), inconsistent with the optimization problem stated directly above it and with the correctly squared first-order condition derived immediately afterward.
- **Expected quote:** Observe that the Lagrangian corresponding to the maximization problem is

$$
\mathcal{L}=w \sum_{\ell=1}^{n} \alpha_{\ell}\left(1+x_{\ell}\right)^{2} \underline{\hat{b}}_{\ell}+\mu\left[C-\sum_{\ell=1...
- **Matched findings (3):**
  - [section-xcheck-5] Lagrangian objective missing square on \hat{\underline{b}}_\ell
  - [notation-tracker] Lagrangian missing squared exponent on b̂_ℓ
  - [formula-cross-checker] Lagrangian in proof of Theorem 1 has b̂_ℓ instead of b̂_ℓ²

### [~] PARTIAL: Unclear notation in proof of Proposition 2

- **Refine score:** 0.8
- **Match confidence:** 0.72
- **Explanation:** LLM judge: Finding #53 captures the core complaint that Δb* is used without definition in the proof of Proposition 2 (and notes it should be y*, which is defined as b*−b̂ earlier). This covers one of the two sub-issues in comment-6. However, neither Finding #53 nor any other finding explicitly calls out the inconsistency between ρ(Δb*, √C u^1) and ρ(Δb*, u^1) — i.e., the switching between a scaled and unscaled reference vector in the cosine-similarity computation. The notation/undefined-symbol aspect is matched; the scaling inconsistency is not.
- **Expected quote:** Cosine similarity. We now turn to the cosine similarity result. We focus on the case of strategic complements. The proof for the case of strategic substitutes is analogous. We start by writing a usefu...
- **Matched findings (1):**
  - [notation-tracker] Δ𝐛* used without definition; should be 𝐲*

