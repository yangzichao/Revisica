Now I have all the material needed. Let me compose the comprehensive review report:

---

# Writing Review: *Targeting Interventions in Networks* (Galeotti, Golub, Goyal)
**Venue profile:** general-academic | **Date:** 2026-04-07

---

## Executive Summary

This is a technically accomplished paper that deploys a spectral/principal-component decomposition to characterize optimal targeting policies in network games. The formal results appear largely sound, but the manuscript has accumulated a significant number of mechanical errors—several of which are **mathematically critical**—alongside structural and rhetorical mismatches with the declared general-academic target venue.

Four tiers of work are needed before resubmission:

1. **Critical formal fixes** (wrong formulas that mis-state the paper's own results): the cosine-similarity definition, Assumption 3's budget threshold, the change-of-variables tilde, the Lagrangian exponent, and the maximizer/minimizer swap.
2. **Pervasive notation cleanup**: the systematic underline-dropping in PC-basis quantities, subscript/superscript swaps, stray symbols (α₂*, Δb*, double-hat, bold β scalar), and two broken LaTeX constructs.
3. **Structural rewrites**: the introduction needs to complete its motivation before diving into model notation; the conclusion needs to cover the stochastic extension and simplicity results it currently omits; Property A needs to be promoted to a formal named assumption.
4. **Venue repositioning**: the abstract, introduction, and conclusion need plain-language bridges for a cross-disciplinary audience; the ALL-CAPS section headers and footnote-heavy literature review signal an Econometrica house style.

---

## Basic Language Issues

| # | Severity | Location | Issue | Fix |
|---|----------|----------|-------|-----|
| L1 | Minor | Abstract | Wrong possessive: `individual's private returns` | → `individuals' private returns` |
| L2 | Minor | §1 intro | Truncated plural possessive: `individual' eigenvector centralities` (missing trailing s) | → `individuals' eigenvector centralities` |
| L3 | Minor | §5 prose | Same error: `Shocks to individual's standalone marginal returns` | → `individuals' standalone marginal returns` |
| L4 | Minor | §3–4 | Misspelling: `faciliates` | → `facilitates` |
| L5 | Minor | §4 | Inconsistent agent label: `the principal's objective` (one occurrence) vs. universal use of `the planner` everywhere else | → `the planner's objective` |
| L6 | Minor | §4 figure ref | Mixed singular/plural: `see Figures 3(B) and Figure 3(D)` | → `see Figures 3(B) and 3(D)` |
| L7 | Major | Abstract ↔ §2 | Terminology drift: Abstract uses `private returns to investment`; body consistently uses `standalone marginal returns of actions`. These are not synonyms; the paper's technical term should appear in the abstract too. | Standardize on `standalone marginal returns` throughout. |
| L8 | Minor | Abstract | The budget constraint is never introduced in the abstract, yet the final sentence conditions a result on `large budgets`—the premise for that result is missing. | Add one clause: *"A utilitarian planner with a limited budget can intervene…"* |
| L9 | Minor | Abstract | `they essentially involve only a single principal component` hedges with *essentially*, but §1 and Propositions 1–2 state **exact** proportionality. | Remove `essentially`, or make explicit this is an asymptotic statement. |
| L10 | Minor | Abstract | Abstract co-bills externalities and strategic spillovers as co-equal drivers; all theorems are governed solely by the spectral structure of strategic interactions. | Clarify that externalities enter welfare but results are driven by the spectral structure of strategic spillovers. |

---

## Structure and Logic Issues

### S1 — Introduction model exposition precedes motivation *(major)*
The second paragraph of §1 launches into full model notation (payoff structure, adjacency matrix, budget constraint form) before the paper has explained why the problem is hard or how prior work falls short. The literature review follows four pages later. **Fix:** Move the detailed model walkthrough to after the high-level results summary and literature positioning. Limit the introduction's model content to 2–3 sentences.

### S2 — Contribution framed as "methodological" only *(major)*
> *"The main contribution of this paper is methodological."*

This undersells the paper's economic substance. The results deliver precise policy-actionable predictions: under strategic complements, target in proportion to eigenvector centrality; under substitutes, exploit bipartite network structure; the spectral gap governs the budget threshold for simplicity. **Fix:** Lead with the substantive economic finding, then describe the PC-decomposition as the analytical vehicle that enables it.

### S3 — Literature review deferred too late and too compressed *(major)*
The review occupies ~one paragraph at the end of §1, with substantive citations delegated to footnotes 4–5. Papers building on Ballester et al. (2006), Bramoullé–Kranton (2007), Allouch (2015/2017), and the CS/sociology targeting literature are not differentiated in text. **Fix:** Expand the review to a dedicated paragraph placed *before* the roadmap, elevating the most important comparisons from footnotes.

### S4 — Property A introduced via examples, not as a named assumption *(major)*
Property A (aggregate equilibrium utility is proportional to sum of squares of equilibrium actions) is the load-bearing technical condition for *all* main results, yet it is derived inductively from examples rather than stated formally upfront. §4 opens by invoking it without warning. **Fix:** State Property A as a named formal assumption in §2, *before* the examples, with a note on which results depend on it. Then *verify* it in Examples 1 and 2.

### S5 — Conclusion omits the stochastic extension entirely *(major)*
The introduction devotes a full paragraph to Propositions 3–4 (incomplete-information extension). The conclusion contains no mention whatsoever of §5, the stochastic setting, or these propositions. **Fix:** Add a sentence acknowledging the incomplete-information contribution, e.g.: *"We also extended the framework to incomplete information (§5), showing in Propositions 3 and 4 that the principal-component ordering insights carry over when the planner knows only the distribution of agents' standalone marginal returns."*

### S6 — Conclusion omits the simplicity/eigenvalue-gap result *(major)*
Propositions 1–2 (simplicity threshold, eigenvalue gap governs budget needed) are named prominently in the introduction but disappear entirely from the conclusion. **Fix:** Add: *"For sufficiently large budgets, the optimal intervention simplifies to a vector proportional to the leading (or trailing) principal component alone, with the eigenvalue gap of the interaction network determining how large that budget threshold needs to be (Propositions 1 and 2)."*

### S7 — Section 5 ends with setup language, not findings *(major)*
The closing sentence of §5 announces what *will be* considered rather than reporting findings. The reader transitions to the conclusion without a resolved takeaway from the incomplete-information extension. **Fix:** Either conclude §5 with a stated proposition, or add a one-sentence bridge summary before closing.

### S8 — Assumption 3's cross-reference: attributes α_ℓ well-definedness to Assumption 1 instead of Assumption 2 *(major)*
> *"Note that, for all ℓ, α_ℓ are well-defined (by Assumption 1)…"*

Assumption 1 only guarantees G is symmetric (real eigenvalues). The no-zero-denominator condition for α_ℓ = 1/(1−βλ_ℓ)² follows from Assumption 2's spectral-radius condition ρ(βG) < 1. **Fix:** Change `(by Assumption 1)` → `(by Assumption 2)`.

### S9 — Residual matrix G^(2) definition is incorrect for the stated sequential PCA claim *(major — see Needs Human Check)*
The paper defines G^(2) = G − u¹(u¹)ᵀ (subtracting the unit-normalized outer product), but the correct residual for the sequential PCA construction is G − λ₁u¹(u¹)ᵀ (subtracting the rank-1 best approximation). As defined, G^(2) has eigenvalues {λ₁−1, λ₂, …, λ_n}, and applying the same minimization to it does not recover u² in general if λ₁ > 2. **Fix:** Define G^(2) = G − λ₁u¹(u¹)ᵀ, or reframe the variational characterization with a ‖u‖=1 constraint.

### S10 — Lemma 1 invokes μ > wα₁ without proof *(major)*
The final bound in Lemma 1 requires the strict inequality μ > wα₁. The proof of Theorem 1 establishes μ ≠ wα_ℓ for all ℓ (no degenerate denominator) but does not explicitly establish the direction of the inequality. **Fix:** At the close of the Theorem 1 proof or the opening of Lemma 1, add: *"Since x_ℓ* ≥ 0 for all ℓ when w > 0, and x_ℓ* = wα_ℓ/(μ−wα_ℓ), we have μ > wα_ℓ for every ℓ; in particular μ > wα₁."*

### S11 — Proposition 2 simplicity bound lacks evidence of tightness *(minor)*
The sufficient condition is derived from a loose inequality; the paper does not assess whether it is approximately tight or provide an example where near-simplicity fails when the bound is violated. **Fix:** Add a short paragraph providing either (a) a family of examples where the bound is approximately achieved, or (b) an explicit acknowledgment that the bound is sufficient-but-not-necessary with guidance on computing the actual threshold.

### S12 — Intuition for status quo effect in Theorem 1 is circular *(minor)*
The stated intuition (convexity of welfare in the PC basis) restates a mathematical property rather than providing economic content. **Fix:** Surface the economic mechanism explicitly: because welfare gain from changing b̲_ℓ is proportional to (1+x_ℓ), and x_ℓ is the relative change, a component already large in the status quo provides a larger base from which marginal changes yield high returns.

### S13 — Corollary 1 not linked to Section 3's clustering/oscillation vocabulary *(minor)*
Section 3 builds the intuition that top eigenvectors capture smooth cluster-level patterns and bottom eigenvectors capture oscillating, negatively-correlated patterns. Corollary 1 is exactly where this vocabulary pays off, but §4 never invokes it. **Fix:** Add a sentence after Corollary 1 connecting the eigenvalue ordering to the structural description in §3.

### S14 — Section roadmap under-describes §2 *(minor)*
`"Section 2 presents the optimal intervention problem"` — but §2 also introduces the game, derives the Nash equilibrium, defines welfare, states Assumptions 1–2, and provides two worked examples. **Fix:** `"Section 2 introduces the model—the game, the Nash equilibrium, the welfare criterion, and the optimal intervention problem—and illustrates it with two economic applications."`

### S15 — Bibliography reference errors *(major)*
- **Banerjee et al. (2013):** fourth co-author listed as `M. O. Duflo`—should be `M. O. Jackson`. The error propagates into the in-text citation in footnote 5.
- **van der Leij (2006):** listed as `van der Leis` in the reference list but cited correctly as `van der Leij` in footnote 4.
- **Galeotti, Golub, Goyal (2020) supplement:** missing comma between second and third author (`B. Golub S. Goyal`).

---

## Scholarly Rhetoric Issues

### R1 — Conclusion advertises extensions without connecting them to the framework *(minor)*
The conclusion introduces a budget-balanced tax/subsidy extension and cites ongoing joint work (Galeotti, Golub, Goyal, Talamaàs, and Tamuz 2020) without explaining what changes in the constraint or what new difficulties arise. **Fix:** Either briefly explain how the budget-balance constraint changes the PC characterization (e.g., which components become infeasible), or remove the reference and confine the future-directions discussion to the network-alteration problem, which is more directly connected to the paper's framework.

### R2 — 'Property A' cited in conclusion as a baseline condition never mentioned in introduction *(minor)*
The conclusion relaxes Property A as a known modeling primitive, but first-time readers who came from the introduction have no referent for it. **Fix:** Either add a parenthetical to the introduction (`"…together with a regularity condition, Property A, which ensures a well-behaved equilibrium response"`), or rephrase the conclusion to describe the condition's content.

---

## Venue-Style Gap

The paper is written in the house style of *Econometrica* / *AER*. The following specific markers create friction with a general-academic outlet:

| Marker | Current | General-Academic Norm |
|--------|---------|----------------------|
| Section headers | ALL CAPS (`THE MODEL`, `OPTIMAL INTERVENTIONS`) | Title case |
| Numbered formal primitives | `Assumption 1`, `Assumption 2`, `Assumption 3` as standalone displayed blocks | Conditions woven into prose; or reduced to one assumption block |
| Footnote density | 17+ footnotes in introduction + body | Minimal; substantive literature comparison in text |
| Abstract | Opens with `eigenvalue decomposition`, `orthogonal principal components` in sentence 2 | Opens with real-world stakes; technical terms introduced only after motivation |
| Introduction length of motivation | < 1 paragraph before model notation | 2–4 paragraphs: question → concrete example → gap in prior work → approach |
| Applications | Two worked mathematical examples inside §2, fully formalized | Foregrounded in the introduction as motivating narratives; revisited concretely in conclusion |
| Contribution framing | `"The main contribution of this paper is methodological"` | Leads with substantive insight; methodology is the means, not the end |
| Conclusion | Recapitulates formal model in technical terms | Translates results into policy guidance; closes with a "so what" paragraph |

**Highest-priority venue fix:** Rewrite the abstract (see Suggested Rewrites §A below) and add a 2–3 paragraph motivating narrative at the top of §1 before any model notation.

---

## Math Verification Issues

The following are *formal errors* confirmed by multiple independent checkers. All require author correction before the paper can be considered mathematically self-consistent.

### MV1 — Cosine similarity definition missing ‖z‖ in denominator *(critical — confirmed ×5)*
**Current:** Definition 1: ρ(**y**, **z**) = **y**·**z** / ‖**y**‖  
**Correct:** ρ(**y**, **z**) = **y**·**z** / (‖**y**‖ · ‖**z**‖)  
As written, ρ is not symmetric, not bounded in [−1,1], and the claimed special cases (ρ=1 iff z is a positive scaling of y) are false for non-unit z. All downstream uses happen to be correct because z = u^ℓ with ‖u^ℓ‖ = 1 in every application, but the general definition is wrong.

### MV2 — Assumption 3 missing squared norm *(critical — confirmed ×4)*
**Current:** `Either w<0 and C<‖b̂‖, or w>0`  
**Correct:** `Either w<0 and C<‖b̂‖², or w>0`  
The preceding sentence correctly states the first-best is achievable when C ≥ ‖b̂‖² (cost of setting every b_i = 0). Footnote 34 also confirms the squared form. As written, the assumption is inconsistent with its own stated motivation.

### MV3 — Self-referential change of variables in Example 2 *(critical — confirmed ×6)*
**Current:** `b_i = [τ − b_i]/2`  (defines b_i in terms of itself)  
**Correct:** `b_i = [τ − b̃_i]/2`  
The immediately following status-quo formula correctly uses b̃_i; the tilde was accidentally dropped in the change-of-variables line. As written, the formula reduces to b_i = τ/3 for all i.

### MV4 — Lagrangian objective term missing exponent 2 on b̲̂_ℓ *(major — confirmed ×6)*
**Current:** ℒ = w Σ α_ℓ (1+x_ℓ)² **b̲̂_ℓ** + μ[C − Σ b̂_ℓ² x_ℓ²]  
**Correct:** ℒ = w Σ α_ℓ (1+x_ℓ)² **b̲̂_ℓ²** + μ[C − Σ b̲̂_ℓ² x_ℓ²]  
The optimization problem immediately above has b̲̂_ℓ², and the FOC below requires b̂_ℓ² to factor out correctly. The downstream proof is unaffected (because b̂_ℓ² cancels in the FOC), but the Lagrangian as printed is internally inconsistent with both the problem and the FOC.

### MV5 — Eigenvectors of minimization problems called "maximizers" *(major — confirmed ×3)*
**Current:** `"the eigenvector u^n is a maximizer of the first problem, while u^{n−1} is a maximizer of the second"`  
**Correct:** Both variational problems are minima; u^n and u^{n-1} are **minimizers**.  
(By contrast, the analogous passage for λ₁ and λ₂ correctly says "maximizer" for the max problems; this appears to be a copy error.)

### MV6 — Sign flip in bottom-gap denominator expression *(major — confirmed ×2)*
**Current:** the term α_{n-1}/(α_{n-1} − α_n) (text discussion)  
**In Proposition 2:** denominator is α_n − α_{n-1} (positive for β<0)  
As written in the discussion, the denominator is negative for β<0, contradicting the proposition. **Fix:** Change to α_{n-1}/(α_n − α_{n-1}).

### MV7 — Missing summation index in cost function K(ℬ) *(major — confirmed ×2)*
**Current:** K(ℬ) = φ(∑_{∈𝒩} σ_{ii}^ℬ)  
**Correct:** K(ℬ) = φ(∑_{i∈𝒩} σ_{ii}^ℬ)

---

## Notation Issues

### N1 — Systematic underline dropped on b̂_ℓ in PC-basis expressions *(major)*
The paper defines b̲ = U⊺b (underline = PC-basis projection). Equation (6) in Theorem 1, the marginal-return/marginal-cost display, the Lagrangian constraint term, the FOC, and equation (13) all write b̂_ℓ² without the underline, conflating the ℓ-th coordinate of b̂ in the original basis with its projection onto the ℓ-th principal component. The IT-PC reformulation (correctly) uses b̲̂_ℓ². **Affected lines:** eq. (6), eq. (13), Lagrangian, FOC, and associated proof lines. Replace b̂_ℓ with b̲̂_ℓ in all PC-basis contexts.

### N2 — Subscript/superscript swap on eigenvector entry u_ℓ^i *(major)*
One occurrence in the proof of Proposition 2 writes u_ℓ^i (subscript ℓ, superscript i) — the paper's convention is u_i^ℓ (subscript = component index, superscript = eigenvector index). Since U is not generally symmetric, u_{ℓi} ≠ u_{iℓ}. **Fix:** Change u_ℓ^i → u_i^ℓ.

### N3 — New symbol Δb* introduced for existing quantity y* *(major)*
The proof of Proposition 2 introduces Δb* = b* − b̂ without definition; Theorem 1's proof already defined y* = b* − b̂ for the same quantity. **Fix:** Replace Δb* with y* throughout the Proposition 2 proof.

### N4 — Transpose and star misplaced in equation (9): (ā⊤)* instead of (ā*)⊤ *(major)*
The equilibrium star should bind more tightly than the transpose. As written, the expression can be misread as a Hermitian adjoint. **Fix:** Change (ā⊤)*(ā*) → (ā*)⊤(ā*).

### N5 — Scalar β incorrectly bolded as 𝛃 in two occurrences *(major)*
β is a scalar throughout the paper but appears as 𝛃 (bold) at two points inside [**I** − **β****Λ**]^{-1}. **Fix:** Use plain β in both occurrences (lines 175 and 436).

### N6 — Non-bold vectors/matrices in equation (2) *(major)*
Equation (2) [I−βG]a* = b uses non-bold I, G, a*, b; the paper's convention bolds all vectors and matrices. Same issue on line 166. **Fix:** Apply consistent bold formatting.

### N7 — Garbled summation subscript in (IT-PC) *(minor)*
`\sum \ell=1^{n}` should be `\sum_{\ell=1}^{n}` (LaTeX markup error dropped subscript braces).

### N8 — Spurious α₂* (starred) in Proposition 2 welfare bound *(minor — confirmed ×4)*
α₂* appears exactly once in an intermediate inequality step; α_ℓ are never starred anywhere else. The supporting calculation uses plain α₂. **Fix:** Replace α₂* → α₂.

### N9 — Double hat b̂̂_ℓ in proof instead of b̲̂_ℓ *(minor)*
One occurrence in the Proposition 2 proof writes `\hat{\hat{b}}_ℓ` (undefined symbol). Context shows it should be `\underline{\hat{b}}_ℓ`.

### N10 — α_ℓ' (prime) misread as derivative instead of α_{ℓ'} *(minor)*
In the Proposition 1 proof, α_ℓ' (with prime as superscript) should be α_{ℓ'} (subscript ℓ-prime indexing a different component).

### N11 — Set 𝒩 written as plain N in one occurrence *(minor)*
`for every i ∈ N, g_{ii} = 0` — should be i ∈ 𝒩.

### N12 — Fact 1 uses weak inequalities (≥) contradicting Assumption 2's strict distinctness *(minor)*
Under Assumption 2, all eigenvalues are distinct, so the ordering should be λ₁ > λ₂ > … > λ_n. The `"For generic G"` qualifier is also misleading under an active assumption. **Fix:** Use strict inequalities and `"Under Assumption 2, the decomposition is uniquely determined"`.

### N13 — Inline draft annotation left inside display equation *(minor)*
`& \text{ see calculation below } D \text{ are positive }` — an author's marginal note accidentally left inside an aligned equation array. **Fix:** Remove from the display; insert as a one-sentence prose justification after the equation chain.

---

## Suggested Rewrites

### A — Abstract (venue rewrite)
> **Current opening:** *"We study games in which a network mediates strategic spillovers and externalities among the players. How does a planner optimally target interventions that change individual's private returns to investment? We analyze this question by decomposing any intervention into orthogonal principal components, which are determined by the network and are ordered according to their associated eigenvalues."*

**Suggested replacement:**
> Networks shape how decisions propagate: an individual's incentive to invest, contribute, or exert effort depends on what her neighbors do. Knowing this, how should a policymaker with a limited budget allocate incentive-changing interventions across a population? We show that the answer depends critically on a single structural feature of the network—its principal components (eigenvectors)—and on whether individuals' decisions are strategic complements or substitutes. When actions reinforce each other, optimal interventions concentrate on globally central individuals (those with high eigenvector centrality); when actions crowd each other out, optimal interventions instead exploit local partitions of the network. For large budgets, the optimal policy collapses to a strikingly simple rule: target a single network statistic. These findings provide actionable guidance for policy design in settings ranging from technology adoption and public-good provision to peer-effects programs in education and public health.

### B — Opening of §2 (audience positioning)
> **Suggested introductory framing before formal payoff notation:**
> *"We study a situation in which n individuals each choose how much effort or investment to exert. The payoff each person receives depends on her own action and, through a network of relationships, on the actions of her neighbors. Strategic complements (β > 0) capture settings where working harder raises the incentive of your neighbors to work harder too—think of researchers sharing a lab or employees in a collaborative team. Strategic substitutes (β < 0) capture settings where your effort reduces your neighbors' incentive—as in competition for a shared resource or a local public good. Formally, the payoff to individual i is: [equation]."*

### C — Contribution paragraph (structure rewrite)
> **Replace:** *"The main contribution of this paper is methodological. It lies in (i) using the principal components approach to decompose the effect of an intervention on social welfare and (ii) using the structure afforded by this decomposition to characterize optimal interventions."*
>
> **With:** *"Our main contribution is to show that the nature of strategic interaction—complements versus substitutes—determines which network statistic governs optimal targeting, and to characterize precisely how large the budget must be for a single network statistic to suffice. Methodologically, this relies on a principal-component decomposition of the planner's objective that decouples the optimization across eigenvectors of the interaction network."*

### D — Conclusion closing paragraph (venue rewrite)
> **Suggested addition:**
> *"Our results carry a practical message for intervention design: the right targeting heuristic depends on both the nature of peer influence and the topology of the social network. When individuals' actions reinforce each other and the network is cohesive (large spectral gap), a simple rule—target the most central individuals—is nearly optimal even with limited budgets. When actions crowd each other out and the network is partitionable into communities, effective targeting instead requires subsidizing one community and discouraging the other. Knowing whether peer effects are complementary or substitutable, and whether the relevant network is cohesive or community-structured, is sufficient to identify the appropriate targeting strategy."*

---

## Needs Human Check

The following issues require author or domain-expert verification before a fix can be confirmed:

| # | Issue | Why human expertise is needed |
|---|-------|-------------------------------|
| H1 | **Residual matrix G^(2) = G − u¹(u¹)ᵀ (§3)**: the sequential PCA claim may not hold unless λ₁ ≤ 1 or a unit-norm constraint is applied. | The correction (use λ₁u¹(u¹)ᵀ instead) changes the stated mathematical claim; authors need to verify which version of the decomposition they intend. |
| H2 | **Proposition 2 bound tightness**: the multiplier 2‖b̂‖² appears as a loose inequality artifact. | Authors should either confirm the bound is qualitatively tight (with an example) or acknowledge it is conservative and bound it tightly in an erratum or revision. |
| H3 | **"Essentially" in the abstract**: whether Propositions 1–2 assert *exact* proportionality or only approximate proportionality for large-but-finite budgets. | The introduction says exact; the abstract says essentially. Only the authors can confirm the intended strength of the result. |
| H4 | **Banerjee, Chandrasekhar, Duflo, and M. O. Duflo (2013)**: fourth author listed as M. O. Duflo — likely should be M. O. Jackson. | Requires bibliographic verification; a wrong author name is a citable error. |
| H5 | **Assumption 3's w < 0 and C < ‖b̂‖ condition**: whether the squared-norm fix (C < ‖b̂‖²) was the authors' intent or whether a normalization convention makes ‖b̂‖ = ‖b̂‖² in their preferred parameterization. | Authors should confirm the parameterization before changing the assumption. |
| H6 | **μ > wα₁ in Lemma 1**: the inequality can be recovered from the FOC sign argument but is not explicitly stated. Authors should confirm the intended proof structure. | The fix (adding an explicit intermediate step) is low-risk but should be verified against the complete proof in the Supplemental Material. |

---

## Revision Priorities

### Tier 1 — Fix before any submission (correctness)
1. **MV3** — Self-referential change of variables: `b_i = [τ−b_i]/2` → `b_i = [τ−b̃_i]/2`
2. **MV1** — Cosine similarity definition: add `‖z‖` to denominator
3. **MV2** — Assumption 3: `C<‖b̂‖` → `C<‖b̂‖²`
4. **MV4** — Lagrangian: add exponent 2 on b̲̂_ℓ in objective term
5. **MV5** — Replace "maximizer" → "minimizer" for λ_n, λ_{n-1} characterization
6. **MV6** — Fix sign in denominator of bottom-gap expression
7. **MV7** — Add missing summation index i in K(ℬ)
8. **S8** — Cross-reference: attribute α_ℓ well-definedness to Assumption 2, not Assumption 1
9. **S15** — Fix three bibliography errors (Jackson, van der Leij, missing comma)

### Tier 2 — Fix before resubmission to general-academic venue (structure/rhetoric)
10. **S1** — Move model exposition after motivation and literature positioning in §1
11. **S2** — Reframe contribution away from purely methodological
12. **S3** — Expand and advance the literature review
13. **S4** — Promote Property A to a formal named assumption in §2
14. **S5 + S6** — Add stochastic extension and simplicity results to the conclusion
15. **S7** — Ensure §5 ends with a result, not setup language

### Tier 3 — Notation cleanup (consistency and readability)
16. **N1** — Restore missing underlines on b̲̂_ℓ throughout PC-basis expressions (eq. 6, eq. 13, Lagrangian, FOC, ~12 proof lines)
17. **N2** — Fix eigenvector index swap u_ℓ^i → u_i^ℓ in Proposition 2 proof
18. **N3** — Replace Δb* with y* in Proposition 2 proof
19. **N4** — Fix (ā⊤)* → (ā*)⊤ in equation (9)
20. **N5** — Un-bold scalar β in two occurrences
21. **N6** — Bold I, G, a*, b consistently in equation (2) and line 166
22. **N7–N13** — Minor cleanup: garbled ∑ subscript, spurious α₂*, double hat, α_ℓ' prime, 𝒩 vs N, Fact 1 strict inequalities, draft annotation in display equation

### Tier 4 — Venue repositioning (general-academic fit)
23. **A** — Rewrite abstract (Suggested Rewrite A above)
24. **B** — Add plain-language motivation before formalism in §2 (Suggested Rewrite B)
25. **C** — Reframe contribution paragraph (Suggested Rewrite C)
26. **D** — Add policy-takeaway closing paragraph to conclusion (Suggested Rewrite D)
27. Convert ALL-CAPS section headers to title case
28. Elevate interdisciplinary applications (CS, sociology, public health) from footnote 5 into the body of the introduction
