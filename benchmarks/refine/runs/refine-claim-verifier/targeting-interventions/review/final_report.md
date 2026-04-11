Here is the merged review report synthesized from all 66 findings files:

---

# Writing Review: "Targeting Interventions in Networks"
**Target venue:** General Academic | **Date:** 2026-04-07

---

## Executive Summary

The paper makes a genuine and elegant contribution—using spectral decomposition to characterize optimal network interventions—but requires a revision pass on three tiers before submission. **Tier 1 (blocking):** four formulas contain verified mathematical errors that produce incorrect numerical results if taken literally (cosine similarity definition, Assumption 3 budget threshold, Lagrangian in Theorem 1 proof, and the "maximizer/minimizer" label in Section 4.2). These must be corrected. **Tier 2 (substantial):** pervasive notation drift (dropped underlines, inconsistent boldface, swapped sub/superscripts, stray symbols) undermines proof legibility throughout; a cluster of structural omissions means the conclusion fails to close the loop on two of the paper's three main results; and two reference errors—one substituting a wrong author name—must be fixed. **Tier 3 (presentation):** the paper frames its contribution as purely methodological and leads with spectral vocabulary before grounding the reader in policy stakes, creating an unnecessary gap with a general academic audience. ~54 of the 66 claim-verification checks came back clean, confirming that the core economic claims are well-supported; the issues are concentrated in proof mechanics, notation, and framing.

---

## Basic Language Issues

### BL-1 · CRITICAL — Cosine similarity definition missing ‖z‖ in denominator
**Where:** Definition 1 (Section 3)
**Problem:** `ρ(y, z) = (y · z) / ‖y‖` omits the norm of the second argument. Numerically: for parallel vectors y = [1,2,3], z = [2,4,6] the formula returns 7.48 instead of 1. The error is invisible in the rest of the paper only because the second argument is always a unit eigenvector.
**Fix:** `ρ(y, z) = (y · z) / (‖y‖ · ‖z‖)`
*(Sources: basic, formula-cross-checker, notation-tracker, math-claim-verifier — 4 independent confirmations)*

### BL-2 · MAJOR — Possessive plural "individual's" where "individuals'" is required
**Where:** Abstract ("individual's private returns"), Section 5 ("Shocks to individual's standalone marginal returns"), Section 3 ("the vector of individual' eigenvector centralities")
**Fix:** Replace every instance of `individual's` and `individual'` with `individuals'`.

### BL-3 · MAJOR — Inconsistent core term: "private returns to investment" vs. "standalone marginal returns"
**Where:** Abstract uses "private returns to investment"; the rest of the paper uses "standalone marginal returns"
**Fix:** Replace "private returns to investment" in the abstract with "standalone marginal returns".

### BL-4 · MAJOR — "Status quo actions b̂" mislabels b̂ as actions rather than payoff primitives
**Where:** Sections 4 and 4.2 nonnegativity paragraph ("As long as the status quo actions b̂ are positive…")
**Fix:** Replace with "status quo standalone marginal returns b̂".

### BL-5 · MINOR — Typos and minor grammar
| ID | Location | Error | Fix |
|----|----------|-------|-----|
| BL-5a | Section 2 | `firstorder` | `first-order` |
| BL-5b | Section 3 | `faciliates` | `facilitates` |
| BL-5c | Section 4 figure caption | `see Figures 3(B) and Figure 3(D)` | `see Figures 3(B) and 3(D)` |
| BL-5d | Section 4.2 | "negatively correlated among neighboring nodes" (ambiguous) | "assign opposite-sign entries to neighboring nodes" |

### BL-6 · MAJOR — Reference errors
| ID | Location | Error | Fix |
|----|----------|-------|-----|
| BL-6a | References | `Banerjee, A., …, M. O. Duflo (2013)` — fourth author listed as Duflo (already listed as third author) | Change `M. O. Duflo` to `M. O. Jackson` |
| BL-6b | References | `B. Golub S. Goyal (2020)` — missing comma | Change to `B. Golub, S. Goyal` |

---

## Structure and Logic Issues

### SL-1 · CRITICAL — Lagrangian in proof of Theorem 1 missing exponent; FOC cannot be derived from it
**Where:** Appendix, proof of Theorem 1
**Problem:** The Lagrangian reads `L = w Σ α_ℓ(1+x_ℓ)² b̲̂_ℓ + μ[C − Σ b̂_ℓ² x_ℓ²]` but the optimisation problem above it has `b̲̂_ℓ²`. The first-order condition `0 = 2b̂_ℓ²[wα_ℓ(1+x*_ℓ) − μx*_ℓ]` cannot be derived from the Lagrangian as written.
**Fix:** Replace `b̲̂_ℓ` with `b̲̂_ℓ²` in the first sum of the Lagrangian.
*(Sources: section-xcheck-3, -5, -12, -13, formula-cross-checker, notation-tracker, math-claim-verifier — 7 independent confirmations)*

### SL-2 · CRITICAL — Assumption 3 uses unsquared norm, contradicting its own purpose
**Where:** Assumption 3 (Section 4)
**Problem:** Assumption 3 states "Either w < 0 and C < ‖b̂‖, or w > 0." The prose immediately above (and the first-best condition) uses ‖b̂‖². With b̂ = (0.3, 0.4, 0.5): ‖b̂‖ ≈ 0.71 and ‖b̂‖² ≈ 0.50, so C = 0.6 satisfies the stated Assumption 3 yet the first-best is achievable—contradicting the assumption's purpose.
**Fix:** Change to "Either w < 0 and C < ‖b̂‖², or w > 0."
*(Sources: section-xcheck-2, -4, -10, formula-cross-checker, notation-tracker, math-claim-verifier, claim-verify-claim-20 — 7 confirmations with numerical proof)*

### SL-3 · CRITICAL — u^n and u^{n-1} labelled "maximizers" of problems that ask for the minimum
**Where:** Section 4.2, paragraph on strategic substitutes
**Problem:** The text defines λ_n = min_{‖u‖=1} Σ g_ij u_i u_j and then states "u^n is a maximizer of the first problem." This is the wrong label—u^n achieves the minimum.
**Fix:** Replace both occurrences of "maximizer" with "minimizer".
*(Sources: formula-cross-checker, notation-tracker, math-claim-verifier — numerically verified on a 4-node path graph)*

### SL-4 · MAJOR — Residual matrix G^{(2)} missing eigenvalue scalar (breaks iterative PCA)
**Where:** Section 3, iterative decomposition paragraph
**Problem:** `G^{(2)} = G − u¹(u¹)ᵀ` drops the scalar λ₁. The rank-1 component is λ₁·u¹(u¹)ᵀ.
**Fix:** Change to `G^{(2)} = G − λ₁ u¹(u¹)ᵀ`.

### SL-5 · MAJOR — r*_ℓ used in Corollary 1 without ever being defined
**Where:** Corollary 1 (Section 4)
**Fix:** Add before Corollary 1: "Define r*_ℓ ≡ ρ(y*, u^ℓ(G)) / ρ(b̂, u^ℓ(G)) as the ratio of the optimal intervention's alignment to the status quo's alignment with the ℓ-th principal component."

### SL-6 · MAJOR — Conclusion fails to close the loop on two main results
**Where:** Section 6
**Problem:** (a) The stochastic extension (Propositions 3 & 4, Section 5) receives zero acknowledgement in the conclusion. (b) The large-budget simplicity result (Propositions 1 & 2) is similarly absent despite being featured in the introduction.
**Fix:** Add two sentences: one summarising that incomplete information preserves the spectral ordering of optimal interventions, and one recapping the large-budget single-component result.

### SL-7 · MAJOR — α_ℓ well-definedness attributed to wrong assumption
**Where:** Section 4, sentence introducing α_ℓ
**Problem:** The text attributes α_ℓ's well-definedness to Assumption 1 (symmetry), but it is Assumption 2 (spectral radius < 1) that guarantees |βλ_ℓ| < 1 and hence 1−βλ_ℓ ≠ 0.
**Fix:** Change "(by Assumption 1)" to "(by Assumption 2, which implies |βλ_ℓ| < 1 for all ℓ)".

### SL-8 · MAJOR — Abstract claims general decomposition; requires symmetric matrix
**Where:** Abstract vs. Conclusion
**Problem:** The abstract states "decomposing any intervention into orthogonal principal components" without qualification. The conclusion discloses that the entire analysis requires a symmetric interaction matrix.
**Fix:** Add qualifier in abstract: "Under a symmetric interaction matrix, any intervention can be decomposed into orthogonal principal components…"

### SL-9 · MINOR — "Global/local structure" assertion lacks formal grounding
**Where:** Introduction and Section 3
**Problem:** "The higher principal components capture the more global structure of the network" is asserted without a formal definition of "global/local structure" or a citation.
**Fix:** Either add a formal definition, or change to a guarded statement with a forward reference or citation to spectral graph theory literature.

### SL-10 · MINOR — Nonnegativity caveat is an orphaned aside
**Where:** Section 4, paragraph beginning "In some problems, there may be a nonnegativity constraint…"
**Fix:** Relocate as a Remark following Assumption 3.

### SL-11 · MINOR — Garbled annotation left in proof of Proposition 2
**Where:** Appendix, proof of Proposition 2
**Problem:** The text contains "≤ 1 + 2‖b̂‖²/C · (…) see calculation below D are positive"—an author's working note that was never resolved.
**Fix:** Remove annotation; replace with justification: "since (2α₁−α₂)/α₁ ≤ 2, as α₂ > 0".

---

## Scholarly Rhetoric Issues

### SR-1 · MAJOR — "Main contribution is methodological" framing undersells the paper
**Where:** Introduction (contribution paragraph) and Section 6 opening
**Problem:** Twice the paper announces "The main contribution of this paper is methodological." This is self-deprecating framing for a paper with three substantive results about when planners should target hubs vs. periphery nodes.
**Fix:** Replace with three bullet-pointed substantive results:
> "(i) Under strategic complements, optimal interventions concentrate on the most-connected components of the network; under substitutes, on the least-connected. (ii) For sufficiently large budgets, the optimal intervention reduces to a single principal component and is invariant to status quo incentives. (iii) Under incomplete information, the planner should weight components with higher variance more heavily."

### SR-2 · MAJOR — Literature review lists papers without identifying the research gap
**Where:** Introduction, paragraph 3
**Problem:** The paragraph summarises two decades of network-game research without specifying which limitation this paper addresses.
**Fix:** State the gap first ("Existing work characterises equilibria given exogenous parameters; no paper characterises the *optimal* parameter assignment problem"), then position the paper's contribution.

### SR-3 · MAJOR — Masculine pronouns for generic agents
**Where:** Throughout ("his eigenvector centrality", "his effort", "his action")
**Fix:** Replace "his" with "their" throughout.

### SR-4 · MINOR — Keyword "peer effects" absent from abstract text
**Where:** Keyword list
**Fix:** Either add a sentence mentioning peer effects in the abstract, or remove the keyword.

### SR-5 · MINOR — Conclusion introduces two undeveloped applications without connecting them to the paper's method
**Where:** Section 6, final paragraph
**Fix:** Either add one sentence per application explaining how the PC framework applies, or drop the applications and expand the stochastic-extension summary (see SL-6).

---

## Venue-Style Gap

The paper targets a general academic audience (e.g., Econometrica) but several presentational choices narrow the readership unnecessarily.

### VG-1 · CRITICAL — Abstract leads with spectral vocabulary before establishing stakes
**Current:** "We study games in which a network mediates strategic spillovers… decomposing any intervention into orthogonal principal components… eigenvalues of the network of strategic interactions."
**Problem:** A general reader encounters four technical terms before learning why optimal targeting matters.
**Suggested opening:**
> "A planner choosing how to subsidise or tax individuals in a network faces a targeting problem: limited resources must be allocated across individuals whose payoffs interact strategically. We show that the solution is governed by the spectral structure of the interaction matrix…"

### VG-2 · MAJOR — Introduction pivots to model exposition in the second paragraph
**Current:** "We now lay out the elements of the model in more detail…"
**Fix:** Compress model preview to one high-level paragraph and move all notation to Section 2. Use freed space for a two-paragraph intuition build-up before the technical road-map.

### VG-3 · MAJOR — "Spectral gap" introduced as a formal object without lay bridge
**Where:** Propositions 1–2 discussion
**Fix:** Before introducing the spectral gap formally, add: "Intuitively, the spectral gap measures how separated the network's leading structural pattern is from the others; a larger gap means the network has one dominant mode of interaction."

### VG-4 · MINOR — Abstract and Conclusion both open with a different framing sentence; the conclusion's opening reads as a near-repeat of the abstract
**Fix:** Revise the conclusion's opening sentence to synthesise the policy takeaway: "A planner with access to the network's eigenvectors and a sufficient budget should concentrate resources on the principal component whose alignment with the planner's objective is sharpest."

---

## Math Verification Issues

*(Findings from the formula cross-checker and math claim verifier)*

| ID | Severity | Location | Finding | Status |
|----|----------|----------|---------|--------|
| MV-1 | Critical | Definition 1 | Cosine similarity denominator incomplete — numerically produces wrong value for non-unit second argument | **Verified error** |
| MV-2 | Critical | Assumption 3 | ‖b̂‖ vs ‖b̂‖² — numerical counterexample constructed | **Verified error** |
| MV-3 | Critical | Lagrangian (Theorem 1 proof) | b̲̂_ℓ vs b̲̂_ℓ² — FOC incompatible with Lagrangian as written | **Verified error** |
| MV-4 | Critical | Section 4.2 | "maximizer" vs. "minimizer" — verified on 4-node path graph | **Verified error** |
| MV-5 | Major | Section 4.2, discussion | α_{n-1}/(α_{n-1}−α_n) has opposite sign to Proposition 2's α_{n-1}/(α_n−α_{n-1}) | **Verified sign flip** |
| MV-6 | Major | Footnote 24 | Norm decomposition identity `‖(1/n)b̂‖² = (mean)² + Σ(dev)²` is dimensionally wrong; numerical counterexample: b̂=(1,2,3), n=3 gives LHS≈1.56, RHS=6.0 | **Verified error** |
| MV-7 | Minor | Footnote 16 / Corollary 1 discussion | Claim that `x_ℓ/x_{ℓ+1}` is "decreasing in β for substitutes" — symbolic verification shows ratio is increasing in β for both regimes; decreasing in \|β\| for substitutes is the correct statement | **Needs human check** (see below) |

---

## Notation Issues

### NI-1 · CRITICAL — Self-referential change of variables in Example 2
`b_i = [τ − b_i]/2` defines b_i in terms of itself. → Change to `b_i = [τ − b̃_i]/2`.

### NI-2 · MAJOR — Systematic underline drift on b̂_ℓ in PC-basis equations
The paper uses three forms interchangeably for the same object (the projection of b̂ onto the ℓ-th eigenvector): b̲̂_ℓ, b̂_ℓ (no underline), and the hat/underline swapped. **Adopt b̲̂_ℓ (hat over underline) as canonical and apply uniformly throughout Sections 4–5 and the Appendix.**

### NI-3 · MAJOR — Eigenvector entry subscript/superscript inverted in proof
**Where:** Proof of Proposition 2 (line 584)
`u_ℓ^i` used where convention (line 186) prescribes `u_i^ℓ`. → Change to `u_i^ℓ`.

### NI-4 · MAJOR — Undefined notation Δb* used in proof of Proposition 2
`ρ(Δb*, √C u¹)` appears without definition. → Either replace Δb* with y* (the established symbol), or add: "where Δb* ≡ b* − b̂ = y*".

### NI-5 · MAJOR — Stray asterisk: α₂* should be α₂
**Where:** Intermediate welfare bound in Proposition 2 proof. `(2α₁−α₂*)/α₁` — the star has no meaning here. → Remove star: `(2α₁−α₂)/α₁`.

### NI-6 · MAJOR — Double-hat typo b̂̂_ℓ
**Where:** Proof of Proposition 2, the expression for D. → Change `b̂̂_ℓ` to `b̲̂_ℓ`.

### NI-7 · MAJOR — β incorrectly boldfaced as a matrix in one instance
`[I−β̲Λ]⁻¹` — β is a scalar. → Remove boldface/underline from β in this expression.

### NI-8 · MAJOR — Prime on wrong symbol: α_ℓ' should be α_{ℓ'}
**Where:** Proof of Proposition 1, ratio formula. → Change `α_ℓ'` to `α_{ℓ'}`.

### NI-9 · MINOR — Weak eigenvalue ordering (≥) in Fact 1 contradicts Assumption 2's strict distinctness
Fact 1: `λ₁ ≥ λ₂ ≥ ··· ≥ λ_n`. Under Assumption 2, all eigenvalues are distinct. → Replace with strict inequalities `λ₁ > λ₂ > ··· > λ_n`.

### NI-10 · MINOR — Transposition/star ordering inconsistency across sections
Section 4: `(a*)ᵀa*`; Section 5: `(ā^⊤)*(ā*)`. → Standardise to `(a*)^⊤ a*` throughout.

### NI-11 · MINOR — W(b, G) vs W(b; G) separator inconsistency
Sections 4 and 5 use different separators for the same function. → Standardise to `W(b, G)`.

### NI-12 · MINOR — Missing subscript i in summation index
`K(B) = φ(Σ_{∈𝒩} σ^B_{ii})` → Change `Σ_{∈𝒩}` to `Σ_{i∈𝒩}`.

---

## Suggested Rewrites

### RW-1 — Abstract (opening sentence, policy stake, and terminology alignment)
> **Current:** "We study games in which a network mediates strategic spillovers and externalities among the players."
>
> **Suggested:** "A planner who can adjust individuals' standalone incentives in a network faces a fundamental targeting question: where to concentrate limited resources. We study this problem in network games where a symmetric interaction matrix mediates strategic spillovers and pure externalities, and show that the answer is governed by the spectral decomposition of that matrix."

### RW-2 — Contribution statement (Introduction)
> **Current:** "The main contribution of this paper is methodological. It lies in (i)…(ii)…"
>
> **Suggested:** "Our three main results are: (i) The optimal intervention tilts toward higher (lower) principal components under strategic complements (substitutes)—concentrating resources on central (peripheral) individuals. (ii) For large enough budgets, the optimal intervention reduces to a single principal component and is invariant to status quo incentives and to the specific network within an eigenvalue-gap class. (iii) Under incomplete information about standalone returns, the planner should weight components with greater prior variance more aggressively."

### RW-3 — Assumption 3 (corrected)
> **Current:** "Either w < 0 and C < ‖b̂‖, or w > 0."
>
> **Corrected:** "Either w < 0 and C < ‖b̂‖², or w > 0."

### RW-4 — Section 4.2 maximizer/minimizer
> **Current:** "the eigenvector u^n is a maximizer of the first problem, while u^{n-1} is a maximizer of the second"
>
> **Corrected:** "the eigenvector u^n is a **minimizer** of the first problem, while u^{n-1} is a **minimizer** of the second"

### RW-5 — Conclusion opening (synthesising policy takeaway)
> **Current:** "The main contribution of the paper is methodological…"
>
> **Suggested:** "This paper shows that the spectral structure of the interaction network is the key determinant of optimal targeting. A planner with sufficient budget should concentrate resources on the eigenvector component that best aligns with the planner's objectives: the top component under complementarities, the bottom component under substitutabilities. When information about individuals' standalone returns is incomplete, the same logic applies but with components re-weighted by their prior variance."

---

## Needs Human Check

| ID | Issue | Why Human Judgment Needed |
|----|-------|---------------------------|
| HC-1 | **Comparative static in Footnote 16 / Corollary 1 discussion:** claim that x_ℓ/x_{ℓ+1} is "decreasing in β for substitutes" | Automated verification found the ratio is increasing in β for all β; the correct statement may involve \|β\|. Author should confirm the intended claim and which variable (β or \|β\|) the monotonicity refers to. |
| HC-2 | **Footnote 24 norm decomposition:** the stated identity ‖(1/n)b̂‖² = (mean)² + variance appears dimensionally inconsistent | A numerical counterexample was constructed, but the author may have intended a different normalization. Confirm whether the intended identity is ‖b̂‖² = n·(mean)² + Σ(b̂_i − b̄)². |
| HC-3 | **"Global/local structure" claim (SL-9):** whether a formal definition is required or whether this is an established phrase in spectral graph theory that can remain informal | If published in Econometrica, referees may ask for a formal definition; the author should decide whether to add one. |
| HC-4 | **Garbled annotation in Proposition 2 proof:** "see calculation below D are positive" | The intended intermediate step must be reconstructed from context; only the author can confirm the intended logical chain. |
| HC-5 | **Property A and the conclusion:** the conclusion mentions relaxing Property A in extensions, but Property A is never introduced in the introduction | Author should decide whether Property A is central enough to flag earlier or sufficiently peripheral to omit from the conclusion. |
| HC-6 | **Two further applications in conclusion (crime, public goods provision):** whether to expand, retain as-is, or remove | A policy judgment about scope; automated review cannot assess whether these add value without seeing the Supplemental Material. |

---

## Revision Priorities

| Priority | Item | Type | Estimated Effort |
|----------|------|------|-----------------|
| **P1** | Fix Definition 1: add ‖z‖ to denominator (BL-1, MV-1) | Formula error | 2 min |
| **P2** | Fix Assumption 3: add ² to ‖b̂‖ (SL-2, MV-2) | Formula error | 2 min |
| **P3** | Fix Lagrangian: add ² to b̲̂_ℓ in objective (SL-1, MV-3) | Formula error | 5 min |
| **P4** | Fix "maximizer" → "minimizer" ×2 in Section 4.2 (SL-3, MV-4) | Label error | 2 min |
| **P5** | Fix Example 2 change of variables: b_i → b̃_i on RHS (NI-1) | Formula error | 2 min |
| **P6** | Fix Banerjee et al. (2013): "M. O. Duflo" → "M. O. Jackson" (BL-6a) | Reference error | 2 min |
| **P7** | Fix denominator sign in Section 4.2 discussion (MV-5) | Sign error | 5 min |
| **P8** | Resolve all notation drift: NI-2 through NI-12 (underlines, boldface, sub/superscripts, stray symbols) | Notation cleanup | 45–60 min |
| **P9** | Define r*_ℓ before Corollary 1 (SL-5) | Definitions | 5 min |
| **P10** | Add missing eigenvalue scalar to G^{(2)} (SL-4) | Logic error | 5 min |
| **P11** | Fix Footnote 24 norm identity (HC-2) | Formula error | 10 min |
| **P12** | Add conclusion sentences for stochastic extension and large-budget result (SL-6) | Writing | 10 min |
| **P13** | Replace "methodological contribution" framing with substantive results (SR-1) + RW-2 | Rhetoric | 20 min |
| **P14** | Revise abstract for policy stake and correct all terminology (BL-2, BL-3, SL-8, RW-1) | Writing | 20 min |
| **P15** | Fix "his" → "their" throughout (SR-3) | Language | 10 min |
| **P16** | Investigate and resolve HC-1 (monotonicity in β vs \|β\|) | Math check | 30 min |
| **P17** | Resolve HC-4 (garbled proof annotation) and HC-5 (Property A) | Author judgment | 20 min |
| **P18** | Add lay bridge for spectral gap before formal definition (VG-3) | Exposition | 15 min |

> **Total estimated revision time:** ~4–5 hours for P1–P15 (mechanical + writing fixes); P16–P18 require author judgment and may need additional derivation work.
