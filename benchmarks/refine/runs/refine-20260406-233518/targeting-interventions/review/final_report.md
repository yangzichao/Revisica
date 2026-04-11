I now have all the material needed. Let me synthesize everything into the final review report.

---

# Writing Review Report: *Targeting Interventions in Networks*

**Venue profile:** `general-academic`
**Draft file:** `targeting-interventions.md`
**Review date:** 2026-04-06

---

## Executive Summary

This is a technically rigorous paper on optimal network intervention design using spectral decomposition. The core results—characterizing optimal interventions through principal components and connecting the complement/substitute dichotomy to top/bottom eigenvectors—are genuinely novel and policy-relevant. However, the draft has problems across every reviewed dimension that must be addressed before submission.

**Most urgent** are five mathematical errors that make formal statements incorrect as written: (1) the cosine similarity definition omits ‖**z**‖ from the denominator; (2) Assumption 3 writes ‖**b̂**‖ where the logic demands ‖**b̂**‖²; (3) the variational characterization of λₙ and λₙ₋₁ calls their eigenvectors "maximizers" of minimization problems; (4) the change-of-variables in Example 2 is self-referential; and (5) the Lagrangian in the Theorem 1 proof drops a square on b̂_ℓ. These five issues were independently flagged by *all three* mathematical review agents and carry the highest priority.

Beyond mathematics, the draft is written primarily for specialists in economic theory. For a general-academic audience the abstract front-loads spectral machinery before motivating the policy problem, the literature review is compressed into a single paragraph, and the contribution is self-described as "methodological" without tying it to a substantive policy message. The Introduction and Conclusion both need restructuring to be accessible to readers from public health, sociology, or computer science.

---

## Basic Language Issues

### Critical

| # | Location | Issue | Fix |
|---|----------|-------|-----|
| B1 | Abstract, Intro heading | **Plural possessive typo: "individual'"** — `the vector of individual' eigenvector centralities` | → `individuals' eigenvector centralities` |
| B2 | Abstract | **Singular possessive in abstract:** `interventions that change individual's private returns` | → `individuals' private returns` |

### Major

| # | Location | Issue | Fix |
|---|----------|-------|-----|
| B3 | Assumption 3 | **Wrong norm type:** states `C < ‖b̂‖` (unsquared). The preceding paragraph, cost function, and footnote 34 all use ‖b̂‖². The condition as written has incorrect units and is logically inconsistent. | → `C < ‖b̂‖²` |
| B4 | Example 2 | **Circular change-of-variables:** `bᵢ = [τ − bᵢ]/2` defines bᵢ in terms of itself (implying bᵢ = τ/3). The status-quo companion on the same line correctly uses b̃ᵢ. | → `bᵢ = [τ − b̃ᵢ]/2` |
| B5 | Definition 1 | **Cosine similarity missing ‖z‖:** `ρ(y, z) = (y·z)/‖y‖` is the scalar projection of z onto ŷ, not cosine similarity. As stated it is non-symmetric, unbounded, and contradicts the immediately following claim that ρ = 1 iff z is a positive scalar multiple of y. | → `ρ(y, z) = (y·z)/(‖y‖ ‖z‖)` |
| B6 | Section 2 (self-loops paragraph) | **Notation inconsistency:** `for every i ∈ N, gᵢᵢ = 0` uses plain **N** while the rest of the paper uses calligraphic 𝒩 defined on the same page. | → `i ∈ 𝒩` |
| B7 | Post-Prop. 2 discussion | **Denominator sign flip in strategic-substitutes discussion:** text writes `αₙ₋₁/(αₙ₋₁ − αₙ)`, which is *negative* when β < 0 (since αₙ > αₙ₋₁). Proposition 2 itself correctly states `αₙ₋₁/(αₙ − αₙ₋₁)`. | → `αₙ₋₁/(αₙ − αₙ₋₁)` throughout discussion. |
| B8 | Section 4 (cosine similarity prose) | **Mislabelled variable:** `As long as the status quo actions b̂ are positive` — **b̂** is the vector of status quo *standalone marginal returns*, not actions. | → `status quo standalone marginal returns b̂` |

### Minor

| # | Location | Issue | Fix |
|---|----------|-------|-----|
| B9 | Section 4 | Misspelling: **`faciliates`** | → `facilitates` |
| B10 | Section 5 | Plural possessive: `Shocks to individual's standalone marginal returns` | → `individuals'` |
| B11 | Bibliography, Demange (2017) | Journal name: **`Games and Economic Behaviour`** (British) vs. `Games and Economic Behavior` (correct, used in two other entries) | → `Behavior` |
| B12 | Bibliography, Galeotti et al. (2020) | Missing comma: `B. Golub S. Goyal` | → `B. Golub, S. Goyal` |
| B13 | Bibliography | Typo in affiliation: **`Department of Eonomics`** | → `Economics` |

---

## Structure and Logic Issues

### Major

**S1 — Introduction front-loads model mechanics before policy motivation** *(structure + venue agents both flag this)*

The second paragraph of the Introduction immediately presents the formal model (simultaneous-move game, spillovers, adjacency matrix, cost separability) before establishing *why* the targeting problem is difficult or consequential. Readers outside economic theory face notation before motivation. Move the two economic applications (or a brief verbal version) before the model paragraph, and use the Introduction to establish the stake (direct effects vs. strategic feedback cascades) in plain language.

**S2 — Contribution statement buried mid-introduction, after the literature survey**

The primary contribution claim appears only after the literature-review paragraph, subordinating it structurally. In economic theory papers the contribution is conventionally stated in the first two to three paragraphs. Move the contribution statement earlier and add the economic punchline (complement/substitute asymmetry and its policy implications) before the related-literature discussion.

**S3 — Differentiation from Ballester–Calvó-Armengol–Zenou (2006) not explicit**

Both papers identify a specific network statistic for optimal targeting under strategic complements. The contribution paragraph does not explain whether the present paper's first-eigenvector result for complements *subsumes or extends* the Katz–Bonacich targeting result, or whether it is a re-derivation in a different framework. Add one sentence explicitly stating the advance: e.g., the principal-component framework unifies complements and substitutes in a single budget-constrained characterization and characterizes the *full ordering* of components, not just the top one.

**S4 — Property A dispensability claimed but left unsupported**

The text asserts Property A "is not essential" and points to Supplemental Section OA3.1, but the main text's entire formal development assumes Property A. Without a brief summary of what OA3.1 achieves (which results extend, under what conditions, whether qualitatively new phenomena arise), the claim functions as an unverifiable reassurance. Add one to two sentences of substance here.

### Minor

**S5 — "Simple" used informally before formal definition**

The word "simple" is used in the abstract and introduction as an informal adjective before Definition 2 gives it a precise technical meaning (proportional to a single principal component). Add a parenthetical on first informal use: e.g., *"(in the sense made precise in Definition 2 below)"*.

**S6 — Eigenvector centrality / "global contributions" intuition lacks formal anchor**

The claim that targeting in proportion to eigenvector centrality targets "global contributions to strategic feedbacks" is offered as intuition with no citation or derivation. Briefly reference the Neumann-series expansion of [**I** − β**G**]⁻¹ that makes this precise, or add a footnote.

**S7 — Section 5 (Incomplete Information) disconnected from Section 4**

Section 5 opens with one transitional sentence and then introduces a new probability space. There is no prior signal at the end of Section 4 (or in the roadmap) that a stochastic extension is coming or why it is the natural next generalization. Add a bridging sentence at the close of Section 4 and a brief economic motivation (e.g., a planner who observes the network topology but not individual productivity draws).

**S8 — "Ongoing work (2020)" citation in conclusion is ambiguous**

The conclusion cites "Galeotti, Golub, Goyal, Talamàs, and Tamuz (2020)" as "ongoing work" with a year in parentheses, creating the appearance of a working paper with an unknown access status. Either supply a full bibliographic citation (with SSRN/URL) or replace the year with "work in progress."

---

## Scholarly Rhetoric Issues

**R1 — Contribution self-described as "methodological" without substantive anchor**

Writing "The main contribution of this paper is methodological" is standard in specialist journals but signals to a general-academic audience that the paper may lack applied relevance. Frame the contribution in two layers: first the substantive insight (what policymakers should do *differently* depending on network structure), then the methodological basis for it.

**R2 — Technical terms used without intuitive glosses throughout body text**

Terms including *principal components*, *eigenvector centrality*, *spectral gap*, *bipartite graph*, and *Katz–Bonacich centrality* appear in high-visibility locations (abstract, Introduction) before or without any plain-language gloss. A general-academic reader from public health or sociology cannot assess relevance without one-sentence intuitive definitions on first use (e.g., *"eigenvector centrality—a measure of how well-connected an individual is relative to other well-connected peers"*).

**R3 — Examples 1 and 2 not connected to core policy message**

The two applications are introduced as illustrations of "model scope" without a closing sentence tying each back to the targeting insight. For Example 1 (strategic complements), note that the planner should raise incentives proportional to eigenvector centrality. For Example 2 (strategic substitutes), note that the planner must differentiate neighboring agents' incentives to avoid crowding out. 

**R4 — Conclusion repeats methodological framing without plain-language synthesis**

The Conclusion largely restates the model setup and technical approach. Restructure it to open with two to three policy-relevant lessons in plain language, with methodological self-assessment and extensions reserved for subsequent paragraphs.

---

## Venue-Style Gap

The draft is calibrated for a specialist economics-theory readership, not a general-academic one. The specific gaps, in order of importance:

1. **Abstract structure:** Jumps to spectral decomposition in sentence two. A general-academic abstract should establish the real-world stakes (public health, education, labor-market policy) in the first one to two sentences, with the method following as the means.

2. **Literature review depth:** The multi-disciplinary citation block (computer science, sociology, public health) is dispatched in three sentences. A general-academic venue expects at least three to five paragraphs engaging each disciplinary thread: what that literature showed, what question it left open, and how the present paper fills that gap. Inline citations should name key works directly in text rather than relegating them to footnotes.

3. **Policy framing of results:** Propositions 1–4 are stated in mathematical language with no plain-language policy corollaries. For a general-academic audience, each major result should be followed by a one- to two-sentence policy translation (e.g., "In cohesive networks—high spectral gap—targeting based on eigenvector centrality alone is near-optimal; in fragmented networks, individually tailored incentives are necessary").

4. **Self-citation framing:** The paper says its contribution is "methodological" in the same paragraph that introduces the results to a broad audience. For general-academic venues, methodological advances must be justified by their substantive implications rather than presented as ends in themselves.

---

## Math Verification Issues

The following errors were independently confirmed by multiple mathematical review agents:

| Severity | Location | Error | Fix |
|----------|----------|-------|-----|
| **Critical** | Definition 1 | Cosine similarity `ρ(y,z) = y·z/‖y‖` — missing `‖z‖`. Non-symmetric, not bounded in [−1,1] for non-unit vectors. The proof of Theorem 1 (line ~490) uses the correct two-norm formula, creating an internal inconsistency. | → `ρ(y,z) = y·z / (‖y‖ ‖z‖)` |
| **Critical** | Assumption 3 | `C < ‖b̂‖` should be `C < ‖b̂‖²` (squaring is required by units and by the first-best threshold stated two lines earlier). | → `C < ‖b̂‖²`; fix footnote 15 similarly. |
| **Critical** | Variational characterization of λₙ, λₙ₋₁ | Calls **u**ⁿ and **u**ⁿ⁻¹ "maximizers" of *minimization* problems. The analogous paragraph for λ₁, λ₂ correctly says "maximizers" of *max* problems. | → "minimizer" (both occurrences) |
| **Critical** | Example 2, change of variables | `bᵢ = [τ − bᵢ]/2` is self-referential. The status-quo formula on the same line correctly uses b̃ᵢ. | → `bᵢ = [τ − b̃ᵢ]/2` |
| **Major** | Theorem 1 proof, Lagrangian | The objective term has b̂_ℓ (first power) but the problem it encodes has b̂_ℓ² (squared). The subsequent FOC derivation depends on factoring out b̂_ℓ², so the written Lagrangian is dimensionally inconsistent with (IT-PC). | Replace b̂_ℓ with b̂_ℓ² in the objective term. |

---

## Notation Issues

The following notation inconsistencies are distinct from the math errors above. They create systematic ambiguity in the formal development:

| Severity | Symbol | Issue | Fix |
|----------|--------|-------|-----|
| **Major** | b̂_ℓ vs. b̲̂_ℓ | The underline notation z̲ = **U**ᵀ**z** (projections onto PC basis) is established but then dropped inconsistently throughout Theorem 1 (eq. 6), its proof (lines ~465, 471, 483, 491), and the Proposition 2 proof. Plain b̂_ℓ (individual ℓ's scalar marginal return) and underlined b̲̂_ℓ (ℓ-th PC projection) are *different quantities*, making affected equations technically incorrect. | Add underline to all PC-indexed b̂_ℓ instances in Theorem 1, the Lagrangian, and Prop. 2 proof. |
| **Major** | β | Bold **β** appears in two places ([**I** − **β**Λ]⁻¹), falsely implying a vector/matrix. β is a scalar throughout. | → plain `β` in both locations |
| **Major** | u_i^ℓ vs. u_ℓ^i | Paper convention (established at line ~186) is u_i^ℓ = i-th entry of ℓ-th eigenvector. Proof of Proposition 2 (line ~584) writes u_ℓ^i (subscripts transposed), meaning the ℓ-th entry of the i-th eigenvector — a different quantity. The very next line in the same proof uses the correct u_i^ℓ. | → `u_i^ℓ` at line ~584 |
| **Major** | Δ**b*** | Used in the proof of Proposition 2 without ever being defined. Everywhere else the optimal intervention vector is **y*** = **b*** − **b̂**. | → Replace `Δb*` with `y*` throughout Prop. 2 proof |
| **Major** | α₂* | Appears once in the Proposition 2 welfare bound. No asterisked amplification factor exists anywhere in the paper; this is a stray character. | → `α₂` |
| **Minor** | Eq. (2) boldface | `[I − βG] a* = b` drops bold formatting for all vectors/matrices. The convention is established at line ~39 and used in eq. (3) immediately following. | → `[**I** − β**G**]**a*** = **b**` |
| **Minor** | α_{ℓ'} vs. α_ℓ' | In Proposition 1 proof, `α_ℓ'` (prime on α) vs. the intended `α_{ℓ'}` (prime inside subscript, denoting the ℓ'-th component). | → `α_{ℓ'}` |
| **Minor** | Σ_{∈𝒩} | Missing summation index in cost function (10): `Σ_{∈𝒩} σᵢᵢ^ℬ`. | → `Σ_{i∈𝒩}` |
| **Minor** | Σ ℓ=1^n | LaTeX rendering artifact: lower bound detached from sigma symbol. | → `\sum_{\ell=1}^{n}` |
| **Minor** | (a̲^⊤)* | Non-standard transpose placement: transpose before asterisk. | → `(a̲*)^⊤ a̲*` |

---

## Suggested Rewrites

### SW1 — Abstract (venue agent)

> **Current:** *"We analyze this question by decomposing any intervention into orthogonal principal components, which are determined by the network and are ordered according to their associated eigenvalues. There is a close connection…"*

> **Suggested:** *"Policymakers must decide which individuals to target when designing network-based interventions—from public health campaigns to educational subsidies. We study this problem in a general model of strategic interaction on networks and provide a complete characterization of the optimal targeting policy. Our approach decomposes any intervention into orthogonal principal components of the interaction matrix, ordered by their eigenvalues. We show that the strategic structure of the game—whether actions are complements or substitutes—determines which principal components receive the most weight in the optimal intervention. For large budgets, optimal interventions simplify dramatically, concentrating on a single network statistic."*

### SW2 — Introduction second paragraph (replace model walkthrough with policy motivation)

> **Current:** *"We now lay out the elements of the model in more detail. Individuals play a simultaneous-move game with continuous actions…"*

> **Suggested:** *"The problem of targeting interventions arises across many domains: a public health authority deciding which neighborhoods to vaccinate first, an education department allocating tutoring subsidies, or a development bank providing microcredit to entrepreneurs in a village network. In each case, actions are strategic: a person's incentive to invest depends on what neighbors do. A policymaker who ignores these feedback loops will mis-target resources. The key difficulty is that intervening on one individual triggers a cascade of strategic responses throughout the network, whose direction and magnitude depend on the network's architecture and whether actions are complements or substitutes."*

*(Shift the current model-walkthrough paragraph to the opening of Section 2.)*

### SW3 — Contribution statement (reframe as two-layered)

> **Current:** *"The main contribution of this paper is methodological. It lies in (i) using the principal components approach to decompose the effect of an intervention on social welfare and (ii) using the structure afforded by this decomposition to characterize optimal interventions."*

> **Suggested:** *"The paper makes both substantive and methodological contributions. Substantively, we show that two network properties—the spectral gap (for strategic complements) and the bottom gap (for strategic substitutes)—determine whether a simple, network-statistic-based policy nearly achieves optimal welfare or whether individually tailored interventions are necessary. Methodologically, we demonstrate that principal components of the interaction matrix provide a natural basis for decomposing the welfare effects of interventions, decoupling what would otherwise be a high-dimensional problem into a sequence of one-dimensional decisions."*

---

## Needs Human Check

The following items require judgment calls or access to materials not available to automated reviewers:

1. **Supplemental Material OA3.1 content.** The paper claims Property A is "not essential" and cites OA3.1, but the main text gives no summary of what that section achieves. Authors should verify: which main results (Theorem 1, Corollaries, Propositions 1–4) extend without Property A, and under what conditions? The current claim is unsubstantiated without at least one sentence of substance in the main text.

2. **Novelty vs. Ballester–Calvó-Armengol–Zenou (2006).** Under strategic complements the optimal large-budget intervention is proportional to the first eigenvector, which is the Bonacich (Katz) centrality vector. Is the present paper's result a strict generalization, a unification, or a re-derivation? The authors need to confirm this is explicitly addressed somewhere accessible in the main text—not only in supplemental or footnotes—and that the specific advance (budget constraint, unified treatment, stochastic extension) is stated.

3. **"Ongoing work (2020)" citation status.** Galeotti, Golub, Goyal, Talamàs, and Tamuz (2020) is cited in the conclusion as ongoing work. Authors must verify: Has this paper since been published or posted as a working paper? If posted, add a full citation with URL. If still in progress at time of submission, change the year reference to "work in progress."

4. **Proof correctness cascade from notation errors.** The five math errors (especially the systematic underline drift on b̲̂_ℓ vs. b̂_ℓ and the Lagrangian missing square) appear to be *display* errors whose downstream derivations use the correct form. Authors should manually verify that the FOC on line ~471, the budget-pinning equation (eq. 6), and the Proposition 2 welfare bound are derived from the corrected Lagrangian and that no intermediate step silently absorbs the inconsistency.

5. **Eigenvalue ordering convention.** The paper orders eigenvalues from greatest to least (λ₁ ≥ λ₂ ≥ ⋯ ≥ λₙ). Under strategic substitutes (β < 0), the *most* negative eigenvalue λₙ produces the *largest* amplification factor αₙ, so the "bottom" principal component is the most influential. Authors should check whether all discussion of "top" and "bottom" components consistently tracks this ordering and that readers from outside spectral graph theory will not invert the terminology.

---

## Revision Priorities

### P0 — Fix before any submission (math correctness)

1. **Definition 1:** Add ‖**z**‖ to cosine similarity denominator → `ρ(y, z) = y·z / (‖y‖ ‖z‖)`.
2. **Assumption 3:** Add squared exponent → `C < ‖**b̂**‖²`; fix footnote 15 to match.
3. **Variational characterization of λₙ, λₙ₋₁:** Change "maximizer" → "minimizer" (two occurrences).
4. **Example 2 change of variables:** Change `bᵢ = [τ − bᵢ]/2` → `bᵢ = [τ − b̃ᵢ]/2`.
5. **Theorem 1 proof Lagrangian:** Change b̂_ℓ → b̂_ℓ² in objective term.

### P1 — High-priority prose and notation (before general-academic submission)

6. **Abstract restructuring** (SW1): Lead with policy stakes, not spectral method.
7. **Introduction second paragraph** (SW2): Replace model walkthrough with policy motivation.
8. **Contribution statement** (SW3): Add two-layer substantive + methodological framing.
9. **Denominator sign fix in Prop. 2 discussion** (B7): `αₙ₋₁/(αₙ − αₙ₋₁)`.
10. **Underline notation drift** (b̂_ℓ vs. b̲̂_ℓ): Systematic fix across Theorem 1, Lagrangian, and Prop. 2 proof.
11. **β boldface** (two locations): Change **β** → β.
12. **Subscript swap u_ℓ^i → u_i^ℓ** in Prop. 2 proof.
13. **Δb* → y*** throughout Prop. 2 proof.
14. **Spurious α₂* → α₂** in welfare bound.
15. **Plural possessive typos** (B1, B2, B10): `individual'` / `individual's` → `individuals'` (three locations).

### P2 — Important but can follow (rhetorical and venue-style)

16. **Literature review expansion**: Three to five substantive paragraphs engaging CS, sociology, public health threads.
17. **Technical-term glosses**: One-sentence intuitive definitions for *eigenvector centrality*, *spectral gap*, *principal component*, *bipartite graph* on first use in Introduction.
18. **Ballester–Calvó-Armengol–Zenou differentiation**: One explicit sentence in contribution paragraph.
19. **Property A dispensability**: One to two sentences summarizing OA3.1's scope and findings.
20. **Section 5 bridge**: Add motivating economic example and structural preview at end of Section 4.
21. **Conclusion restructuring**: Open with two to three plain-language policy lessons.
22. **"Ongoing work" citation**: Resolve status of Galeotti et al. (2020) companion paper.

### P3 — Polish

23. Minor typos: `faciliates` → `facilitates`; `Eonomics` → `Economics`; missing comma in bibliography; `Behaviour` → `Behavior`.
24. Eq. (2) bold formatting: `[I − βG] a* = b` → bold vectors.
25. Prime placement: `α_ℓ'` → `α_{ℓ'}` in Prop. 1 proof.
26. Missing summation index: `Σ_{∈𝒩}` → `Σ_{i∈𝒩}` in eq. (10).
27. Transpose placement: `(a̲^⊤)*` → `(a̲*)^⊤ a̲*`.
28. LaTeX artifact: `\sum \ell=1^n` → `\sum_{\ell=1}^{n}`.
29. Mislabelled variable: "status quo actions **b̂**" → "status quo standalone marginal returns **b̂**."
30. `N` → `𝒩` (one occurrence in self-loops paragraph).
