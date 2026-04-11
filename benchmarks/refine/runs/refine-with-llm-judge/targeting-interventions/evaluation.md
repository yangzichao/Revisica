# Refine Benchmark: targeting-interventions

- Paper: `/Users/zichaoyang/workplace/ReviseAgent/benchmarks/refine_cases/targeting-interventions.md`
- Expected comments: 6
- Our findings: 92
- Recall (matched + partial): 66.7%
- Full recall (matched only): 50.0%

## Expected vs Found

### [X] MISSED: Comparative static claim in Footnote 16

- **Refine score:** 0.8
- **Match confidence:** 0.95
- **Explanation:** LLM judge: No actual finding addresses the comparative static claim in Footnote 16 that the ratio x_ℓ/x_{ℓ+1} is increasing in β for strategic complements and decreasing for substitutes. The findings cover many notation and sign errors but none question or verify the correctness of this specific footnote claim about how budget allocation ratios depend on β.
- **Expected quote:** It can be verified that, for every $\ell \in\{1, \ldots, n-1\}$, the ratio $x_{\ell} / x_{\ell+1}$ is increasing (decreasing) in $\beta$ for the case of strategic complements (substitutes): thus the i...

### [X] MISSED: Limiting direction of intervention in Proposition 1

- **Refine score:** 1.0
- **Match confidence:** 0.92
- **Explanation:** LLM judge: No actual finding raises the issue of whether Proposition 1 establishes ρ→1 or only ρ²→1 as C→∞. The findings touch on the cosine similarity definition (missing ‖z‖) but none question whether the large-budget limiting result in Proposition 1(2a–b) actually yields convergence of ρ itself versus its square.
- **Expected quote:** If $\beta>0$ (the game features strategic complements), then the similarity of $\boldsymbol{y}^{*}$ and the first principal component of the network tends to $1: \rho\left(\boldsymbol{y}^{*}, \boldsym...

### [+] MATCHED: Sign error in discussion of Proposition 2 (substitutes case)

- **Refine score:** 0.8
- **Match confidence:** 0.97
- **Explanation:** LLM judge: Finding #59 ('Denominator ordering flipped: α_{n-1}/(α_{n-1} − α_n) vs α_{n-1}/(α_n − α_{n-1})') identifies exactly the same sign error. It notes that the discussion text at line 301 uses α_{n-1}/(α_{n-1} − α_n), whereas Proposition 2 Part 2 correctly uses the positive denominator α_n − α_{n-1}, and for β<0 the former is negative while the latter is positive.
- **Expected quote:** If the game has the strategic substitutes property, $\beta<0$, then for any $\epsilon>0$, if $C> \frac{2\|\hat{\boldsymbol{b}}\|^{2}}{\epsilon}\left(\frac{\alpha_{n-1}}{\alpha_{n}-\alpha_{n-1}}\right)...
- **Matched findings (1):**
  - [notation-tracker] Denominator ordering flipped: α_{n-1}/(α_{n-1} − α_n) vs α_{n-1}/(α_n − α_{n-1})

### [+] MATCHED: "Maximizer" vs. "minimizer" for smallest eigenvalues

- **Refine score:** 0.4
- **Match confidence:** 0.99
- **Explanation:** LLM judge: Findings #42, #48, and #58 all identify the same wording slip: the eigenvectors u^n and u^{n-1} are called 'maximizers' of the variational characterizations that use 'min', when they should be called 'minimizers'. All three findings note the internal contradiction with the arg min expression appearing in the same sentence.
- **Expected quote:** Turning next to strategic substitutes, recall that the smallest two eigenvalues, $\lambda_{n}$ and $\lambda_{n-1}$, can be written as follows:
$$
\lambda_{n}=\min _{\boldsymbol{u}:\|\boldsymbol{u}\|=1...
- **Matched findings (3):**
  - [math-claim-verifier] 'Maximizer' should be 'minimizer' for bottom eigenvalue characterization
  - [formula-cross-checker] Eigenvectors of min problems called 'maximizers' instead of 'minimizers'
  - [notation-tracker] Minimizer called 'maximizer' for λ_n and λ_{n-1} characterization

### [+] MATCHED: Typo in Lagrangian in proof of Theorem 1

- **Refine score:** 0.4
- **Match confidence:** 0.99
- **Explanation:** LLM judge: Eight separate findings independently identify the missing squared exponent on b̂_ℓ (or b̲̂_ℓ) in the Lagrangian's objective term. Finding #40 is the clearest match; #50 and #85 provide the most detailed cross-referencing with the reformulated IT-PC problem above. Finding #86 additionally notes the implication: the FOC as stated cannot be derived from the Lagrangian as printed, only from the corrected version.
- **Expected quote:** Observe that the Lagrangian corresponding to the maximization problem is

$$
\mathcal{L}=w \sum_{\ell=1}^{n} \alpha_{\ell}\left(1+x_{\ell}\right)^{2} \underline{\hat{b}}_{\ell}+\mu\left[C-\sum_{\ell=1...
- **Matched findings (3):**
  - [math-claim-verifier] Missing square on b̂_ℓ in displayed Lagrangian
  - [section-xcheck-3] Lagrangian writes b̂_ℓ (not squared) in objective term, inconsistent with the stated IT-PC objective and the FOC that follows
  - [formula-cross-checker] Lagrangian objective term missing squared exponent on b̂_ℓ

### [~] PARTIAL: Unclear notation in proof of Proposition 2

- **Refine score:** 0.8
- **Match confidence:** 0.75
- **Explanation:** LLM judge: Finding #65 ('New symbol Δb* introduced for existing quantity y*') covers the core concern that Δb* is not explicitly defined and drifts from the earlier notation y* = b* − b̂. However, the expected issue also flags the textual switch between ρ(Δb*, √C u^1) and ρ(Δb*, u^1) as a distinct source of confusion; no finding specifically addresses that inconsistency in the second argument of the cosine similarity within the proof.
- **Expected quote:** Cosine similarity. We now turn to the cosine similarity result. We focus on the case of strategic complements. The proof for the case of strategic substitutes is analogous. We start by writing a usefu...
- **Matched findings (1):**
  - [notation-tracker] New symbol Δb* introduced for existing quantity y*

