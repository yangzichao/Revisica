Now I have all the material I need. Let me compose the merged review report.

---

# Writing Review Report
**Paper:** "Inference in molecular population genetics" — Stephens & Donnelly (2000)
**Target venue:** General-academic
**Source files reviewed:** structure, venue, basic (all Claude Sonnet); notation-tracker, formula-cross-checker (both Claude Opus)

---

## Executive Summary

This is a technically sophisticated paper introducing a new importance-sampling algorithm for likelihood-based inference in population genetics. The science is strong and the contribution is real, but the manuscript as it stands is an **unprocessed RSS read-paper transcript**: it carries the full institutional apparatus of that unique publication format (attribution header, "Summary." label, five named discussants, vote-of-thanks ceremony, JRSS reference abbreviations), none of which belongs in a general-academic journal. These format issues dominate the revision agenda and must be resolved before any submission.

Beneath the format layer lie **two critical mathematical errors** — a subscript confusion in the Theorem 1 proof (α_{n-1} for α_{k-1}) and a wrong conditioning index in the Chen–Liu weight recursion (H_{−1} for H_{−t}) — that must be corrected independently of venue. A further indexing error in the definition of the history H (H₁ for H_{−1}) and a missing fraction bar in the coalescence-rate derivation are serious enough to confuse careful readers.

The abstract makes a claim ("several orders of magnitude" improvement) that is not uniformly borne out by the empirical results, and Section 5.4 concedes MCMC superiority on the hardest dataset without connecting that concession to the explanatory framework developed later in Section 6.1. Both issues damage the paper's credibility and should be tightened before resubmission.

A full list of prioritised actions appears at the end of this report.

---

## Basic Language Issues

### Spelling and Typography

| # | Severity | Location | Issue | Fix |
|---|----------|----------|-------|-----|
| B1 | **Major** | Throughout (≥7 locations, incl. lines 138, 173, 195, 607, 865, 907, 1030) | "Griffiths-Tavaré" spelled inconsistently: variants include "Griffiths-Tavare" (missing accent), "GriffithsTavaré" (missing hyphen), "GriffithsTavare" (both missing). | Global replace all variants with the canonical "Griffiths-Tavaré". |
| B2 | **Major** | Line 731 (in-text) and line 1264 (reference list) | Author name "Wuif, C." is a systematic misspelling; the correct surname is **Wiuf, C.** (Carsten Wiuf). | Replace every instance of "Wuif" with "Wiuf". |
| B3 | **Major** | Reference list, lines 691–692 | Two distinct Griffiths & Tavaré papers both carry the label "(1994b)". The second ("Sampling theory for neutral alleles in a varying environment") should be "(1994c)", matching in-text citations that already reference a "(1994c)". | Relabel the second entry "(1994c)"; audit all in-text citations for consistency. |
| B4 | **Minor** | Line 179 (mathematical tuple) | Ellipsis written as ". ." (two spaced full stops) instead of the LaTeX command `\ldots`, inconsistent with all other uses. | Replace ". ." with `$\ldots$`. |
| B5 | **Minor** | Subsection headings 3.3 and 6.2 | Period missing after the section number, inconsistent with every other numbered heading ("3.1.", "3.2.", "6.1.", "6.3.", etc.). | Add period: "3.3." and "6.2.". |

### Grammar and Diction

| # | Severity | Location | Issue | Fix |
|---|----------|----------|-------|-----|
| B6 | **Minor** | PIM discussion paragraph | "our IS is actually independent sampling" — since IS expands to "importance sampling", this reads as "our importance sampling is actually independent sampling", a circular and confusing construction. | Rewrite: "our IS scheme in fact amounts to independent sampling from the full conditional distribution of the history…" |
| B7 | **Minor** | Section 6 comparison paragraph | "to design an efficient IS" — "IS" functions here as a bare abbreviation with no head noun. | Add noun: "to design an efficient IS scheme". |
| B8 | **Minor** | Section 3.1 | "form the bases for inference" — non-idiomatic; the standard expression is singular. | Change to "form the basis for inference". |
| B9 | **Minor** | Section 5.4, first sentence | Acronym "NSE" introduced without expansion; its meaning (Nigeria, Sardinia, East Anglia) appears eight lines later. | Expand at first use: "the so-called NSE (Nigeria, Sardinia and East Anglia) data set". |

### Notation and Mathematical Typos

| # | Severity | Location | Issue | Fix |
|---|----------|----------|-------|-----|
| B10 | **Critical** | Line 239 (Theorem 1 proof — mutation backward rate) | Subscript suddenly switches from k to n: the ratio is written as π(α₁,…,α_{n−1},β) / π(α₁,…,α_{n−1},α), but the proof established A_k(t) = (α₁,…,α_{k−1},α) on line 228. The next line correctly reverts to A_k. This conflates sample size n with the current lineage count k. | Replace both occurrences of α_{n−1} with α_{k−1}: `$\frac{\pi(\alpha_1,\ldots,\alpha_{k-1},\beta)}{\pi(\alpha_1,\ldots,\alpha_{k-1},\alpha)}$` |
| B11 | **Critical** | Line 994 (Chen & Liu discussion — recursive weight) | Numerator written as p_θ(H_{−(t−1)} \| H_{−1}) but the explicit product form on the same line, and the forward-time logic, require conditioning on H_{−t}. The subscript −1 is an error for −t. | Change H_{−1} to H_{−t}: `$w_{-t} \equiv w_{-(t-1)}\frac{p_\theta(H_{-(t-1)}\mid H_{-t})}{q_0(H_{-t}\mid H_{-(t-1)})}$` |
| B12 | **Major** | Line 61 and Fig. 1 caption (line 46) — definition of H | History written as (H_{−m}, H_{−(m−1)},…,H₁,H₀) with a **positive** subscript H₁. All subsequent uses of H employ strictly negative indices (equations (1),(15),(25), etc.); line 179 correctly writes H_{−1}. | Change H₁ to H_{−1} in both locations: `$(H_{-m},H_{-(m-1)},\ldots,H_{-1},H_0)$` |
| B13 | **Major** | Lines 249–254 (Theorem 1 proof — coalescence backward rate) | The conditional probability P{Υ_c \| A_k(t)} is displayed with numerator and denominator on separate aligned lines but **without a fraction bar**, making the denominator appear to multiply rather than divide. The analogous mutation derivation (lines 232–234) correctly uses `\frac`. | Wrap in `\frac{}{}` matching the mutation case. |
| B14 | **Major** | Line 452 (Section 5 diagnostics) | Cross-reference "the estimator (8)" should be "(9)". Equation (8) is the integral identity; equation (9) is the Monte Carlo sum. Lines 151, 157, 165, 187, 456, 611, and 658 all correctly cite "(9)". | Change "estimator (8)" to "estimator (9)" on line 452. |
| B15 | **Major** | Remark 1 | "a characterization of π which is…" — Property (e) of Proposition 1 characterises ̂π (the approximate CSD), not the exact π. Using the undecorated symbol contradicts the immediately surrounding discussion. | Change to "a characterization of $\hat{\pi}$ which is…" |
| B16 | **Major** | Line 933 (Beaumont discussion) | Symbol ̂π(θ \| Aₙ) reused for the Rao-Blackwellised posterior density, whereas in the main paper (Definition 1, line 284) ̂π(· \| Aₙ) is the approximate CSD — completely different objects. Additionally, n is reused for the number of MCMC samples, contradicting its established meaning as sample size. | Introduce a distinct symbol (e.g. π̃(θ \| Aₙ) or p̂(θ \| Aₙ)) and replace n for MCMC sample count with M throughout Beaumont's discussion. |
| B17 | **Minor** | Lines 1127 and 1131 (Ventura discussion) | Importance weight defined as w_θ(H) on line 1127 (Roman w) silently becomes ω_θ(H) (Greek omega) three lines later. No separate definition of ω is given. | Replace ω_θ(H) with w_θ(H) on line 1131. |
| B18 | **Minor** | Line 927 (Beaumont discussion) | Denominator written m^{i!}, syntactically ambiguous between m^{(i!)} and (m^i)!. Context (Poisson likelihood for m^i mutations) requires (m^i)!. | Write `$(m^i)!$` with explicit grouping. |

---

## Structure and Logic Issues

### Abstract-Level

**S1 — Critical: "Several orders of magnitude" claim lacks uniform support**

The abstract states the new method achieves efficiency "typically improved by several orders of magnitude". The strongest evidence (Table 1, θ = 15.0; microsatellite constrained problems) supports this. However: (i) at θ = 2.0 both methods perform comparably at 20,000 samples; (ii) Section 5.4 explicitly reports MCMC is *more accurate* for the NSE dataset; (iii) Section 5.5 describes gains of "about an order of magnitude," not several. The word "typically" hedges but is not backed by any aggregate statistic (e.g. effective sample size ratios across all five cases).

**Fix:** Stratify the claim: *"In problems with highly constrained type spaces, efficiency is improved by several orders of magnitude; in less constrained settings, gains of approximately one order of magnitude are observed."* Alternatively, add a summary column to Table 1 reporting ESS ratios so that "typically" has quantitative grounding.

---

**S2 — Major: Abstract conflates Theorem 1 and the SD algorithm without prioritising either**

The sentence "The optimal proposal distribution for these problems can be characterized, and we exploit a detailed analysis of genealogical processes to develop a practicable approximation to it" runs two distinct intellectual contributions — the time-reversal characterisation (Theorem 1) and the SD approximation scheme (Definition 2) — into a single subordinated clause, underselling Theorem 1 as a conceptual anchor with independent significance.

**Fix:** Two sentences: *"We first characterise the optimal IS proposal distribution via time-reversal of the underlying genealogical process (Theorem 1). Building on this characterisation, we derive a computationally practicable approximation that defines a new IS scheme."*

---

### Section-Level

**S3 — Major: Section 5 opening buries the comparison design under a methodological caveat**

The first paragraph of Section 5 (Applications) opens with a justification of why likelihood rather than log-likelihood is reported — a secondary footnote — before stating what the section demonstrates or how the comparison is structured (small exact problems as ground truth, then varying iteration counts). This fragmentation makes the section's logic hard to follow at the outset.

**Fix:** Open with a one-sentence statement of the section's purpose; move the likelihood/log-likelihood justification to a parenthetical or end-of-paragraph note; consolidate the comparison design into a coherent second paragraph.

---

**S4 — Major: Section 5.4 concedes MCMC superiority without a bridge to Section 6.1**

On the largest and most realistic dataset (60 males, three populations, five loci), the MCMC competitor produces more accurate results. This concession is abrupt and unelaborated at the point where it occurs. The explanation (constrained vs. unconstrained tree space) is deferred entirely to Section 6.1, leaving a conspicuous logical gap at the moment of failure.

**Fix:** At the concession in Section 5.4 add: *"This pattern — where MCMC outperforms IS on larger, less constrained problems — is examined in Section 6.1 in terms of tree-space dimensionality."* In Section 6.1, add a corresponding back-reference to the NSE result so the concession becomes part of a principled framework.

---

**S5 — Major: Section 3.4 introduces IS without a transition from the MCMC discussion**

Sections 3.2–3.3 cover two MCMC approaches. Section 3.4 opens cold with a definition of IS, with no bridging sentence positioning IS as an alternative or complement to what precedes it. This is the rhetorical hinge on which the entire paper's contribution turns, and the abrupt pivot weakens the argument precisely where coherence matters most.

**Fix:** Add a transitional sentence: *"An alternative to MCMC for handling missing genealogical data is importance sampling (IS), which addresses expression (4) directly by constructing a proposal distribution over histories."*

---

**S6 — Minor: Introduction roadmap paragraph is not the final paragraph**

The standard convention places the section roadmap as the closing paragraph of an introduction, providing forward momentum. Here, the Edwards (1970) / Whittle (1970) analogy paragraph follows the roadmap, making the introduction feel as if the analogy was an afterthought.

**Fix:** Move the Edwards/Whittle paragraph to immediately precede the roadmap paragraph.

---

## Scholarly Rhetoric Issues

**R1 — Major: Section 6.3 heading "Bells and Whistles" is tonally inconsistent**

Every other section heading in the paper is descriptive and register-neutral ("General," "Extensions," "Diagnostics," "Future Challenges"). "Bells and whistles" is colloquial slang for decorative extras, which is self-deprecating in the live RSS presentation context but out of register for a scholarly journal. The section actually discusses methodologically significant failed IS alternatives and computational strategies.

**Fix:** Rename to "Further Efficiency Improvements and Adaptive Strategies" or "Alternative Proposal Distributions and Computational Heuristics".

---

**R2 — Minor: Citation of Whittle (1970) "in the discussion" assumes RSS insider knowledge**

The phrase "the approach suggested by Whittle (1970) in the discussion of Edwards (1970)" references a formal RSS discussant contribution — a citable scholarly text appended to an RSS read paper. Readers outside the RSS tradition may not understand that "the discussion" is a distinct published contribution rather than a section of Edwards's own paper.

**Fix:** Gloss the reference: *"…the approach suggested by Whittle (1970) — in the published discussion appended to Edwards (1970) — and the approach which we adopt here."*

---

## Venue-Style Gap

The manuscript is currently formatted as an unmodified RSS read-paper transcript. Four issues require immediate correction before any general-academic submission.

| # | Severity | Item | Required Action |
|---|----------|------|-----------------|
| V1 | **Critical** | RSS read-paper attribution header: *"[Read before The Royal Statistical Society at a meeting organized by the Research Section on Wednesday, March 15th, 2000, Professor P. J. Diggle in the Chair]"* | Remove entirely. If submission history must be acknowledged, add a footnote: *"An earlier version of this paper was presented to the Royal Statistical Society Research Section, March 2000."* |
| V2 | **Critical** | Abstract labelled "Summary." (inline JRSS house style) | Replace with a standalone **Abstract** heading, or no heading, per target venue's style guide. The inline "Summary." prefix will cause abstract-parsing errors in most submission systems. |
| V3 | **Major** | Entire "Discussion on the paper by Stephens and Donnelly" section (from line 726 onward), including five named discussants (Wilson, D.A. Stephens, Griffiths, Harding, and others), followed by "The vote of thanks was passed by acclamation." | Remove in its entirety. Substantive scientific points raised by discussants that influenced the manuscript can be acknowledged in a revised Acknowledgements section. If a formal reply was published, it should be omitted or recast as a self-contained authors' rejoinder appendix. |
| V4 | **Major** | Section 6.3 heading "Bells and whistles" (see also R1 above) | Rename with a descriptive, register-neutral heading. |
| V5 | **Minor** | Reference list uses JRSS-specific abbreviated journal titles throughout: "J. R. Statist. Soc. B", "J. Am. Statist. Ass.", "Theor. Popln Biol.", "Stochast. Process. Applic.", etc. | Expand all abbreviated titles to their full forms, or reformat per the target venue's citation style. Current abbreviations will fail automated reference checkers at non-RSS journals. |

---

## Suggested Rewrites

**Abstract — contribution sentences (fixes S2 and S1 together):**

> We first characterise the optimal IS proposal distribution via time-reversal of the underlying genealogical process (Theorem 1). Building on this characterisation, we derive a computationally practicable approximation that defines a new IS scheme. In problems with highly constrained type spaces, the new scheme improves IS efficiency by several orders of magnitude over existing IS algorithms; in less constrained settings, gains of approximately one order of magnitude are observed. The new method also compares favourably with existing MCMC methods in some problems, and less favourably in others, suggesting that both IS and MCMC methods have a continuing role to play in this area.

---

**Section 3.4 opening sentence (fixes S5):**

> An alternative to MCMC for handling missing genealogical data is importance sampling (IS; see Ripley (1987) for background), which addresses expression (4) directly by constructing a proposal distribution over histories. IS is a standard method of reducing the variance of Monte Carlo estimators such as expression (5).

---

**Section 5.4 concession sentence (fixes S4):**

> Further investigation (more runs of each method) suggested that the curve obtained by using micsat is more accurate. This pattern — where MCMC outperforms IS on larger, less constrained problems — is examined in Section 6.1 in terms of tree-space dimensionality.

---

**Whittle citation (fixes R2):**

> …we note an analogy between the approach suggested by Whittle (1970) — in the published discussion appended to Edwards (1970) — and the approach which we adopt here.

---

**Section 6.3 heading (fixes R1 / V4):**

> ### 6.3. Further Efficiency Improvements and Adaptive Strategies

---

**NSE first use (fixes B9):**

> …the so-called NSE (Nigeria, Sardinia and East Anglia) data set considered by Wilson and Balding (1998)…

---

## Needs Human Check

The following items cannot be resolved by textual revision alone and require author or expert judgement:

1. **Adequacy of the "several orders of magnitude" claim (S1).** The reviewers flag that current empirical coverage is uneven. The authors should either supply an aggregate ESS-ratio table covering all five application cases or rewrite the abstract claim. A statistician familiar with the experiments is needed to judge which quantitative summary is most defensible.

2. **Correct interpretation of the coalescence backward-rate display (B13).** The missing fraction bar in lines 249–254 may be a LaTeX rendering artefact rather than a genuine mathematical error. The authors should inspect the original source to confirm whether the `\frac` command is present in the source but dropped by a converter, or genuinely absent.

3. **Beaumont's discussion notation clash (B16).** If Beaumont's contribution is to be retained in any form (e.g., as a rejoinder appendix), the symbol conflict between ̂π as approximate CSD and ̂π as estimated posterior must be resolved. The authors must decide which symbol to reassign and propagate the change consistently.

4. **Chen & Liu and other discussant mathematics (B11, B17, B18).** Errors in the discussant sections (wrong conditioning index, notation drift, ambiguous factorial) were written by third parties. If this material is retained, the original discussants should ideally be contacted to confirm the intended expressions before corrections are finalised.

5. **Scope of the discussant-removal decision (V3).** Removing the Discussion section substantially reduces word count and eliminates several extensions and critiques that may be scientifically valuable. The authors should decide whether to absorb key technical points from discussants into a revised Section 6 or into supplementary material before finalising the manuscript structure.

---

## Revision Priorities

Ordered by urgency and impact:

| Priority | Action | Severity | Notes |
|----------|--------|----------|-------|
| **1** | Remove RSS attribution header, "Summary." label, and entire Discussion/vote-of-thanks block (V1, V2, V3) | Critical | Must be done before any submission attempt |
| **2** | Fix α_{n-1} → α_{k-1} in Theorem 1 proof (B10) | Critical | Mathematical correctness error in a core theorem |
| **3** | Fix H_{−1} → H_{−t} in Chen–Liu weight recursion (B11) | Critical | Mathematical correctness error |
| **4** | Fix H₁ → H_{−1} in definition of H at line 61 and Fig. 1 caption (B12) | Major | Breaks the monotone index sequence throughout |
| **5** | Qualify or substantiate "several orders of magnitude" abstract claim (S1) | Critical | Credibility-damaging overgeneralisation |
| **6** | Separate Theorem 1 and SD algorithm in abstract (S2) | Major | Undersells the theoretical contribution |
| **7** | Fix duplicate reference label (1994b)/(1994c) and "Wuif"→"Wiuf" (B3, B2) | Major | Bibliographic correctness |
| **8** | Fix π → ̂π in Remark 1 (B15); fix ̂π symbol clash in Beaumont (B16) | Major | Notation correctness |
| **9** | Restore fraction bar in coalescence-rate derivation (B13) | Major | Mathematical presentation |
| **10** | Fix "estimator (8)" → "estimator (9)" on line 452 (B14) | Major | Cross-reference error |
| **11** | Add Section 5.4→6.1 forward reference (S4); add 3.4 IS transition sentence (S5) | Major | Logic and coherence |
| **12** | Rename Section 6.3 heading (R1/V4) | Major | Tone and venue alignment |
| **13** | Expand abbreviated journal titles in reference list (V5) | Minor | Venue compliance |
| **14** | Fix global "Griffiths-Tavaré" spelling (B1) | Major | Consistency |
| **15** | Address remaining minor language issues: ellipsis, "basis", NSE, heading periods, ω→w, m^{i!}, etc. (B4–B9, B17–B18) | Minor | Polish pass |
| **16** | Move Edwards/Whittle analogy paragraph before roadmap paragraph (S6); gloss Whittle citation (R2) | Minor | Introduction structure |
