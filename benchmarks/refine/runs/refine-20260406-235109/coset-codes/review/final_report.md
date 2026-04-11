Now I have all the data I need. Let me synthesize the findings from all five review files into a unified Markdown report.

---

# Writing Review: *Coset Codes — Part I* (G. David Forney, Jr.)
### Final Judge's Report · Target Venue: General Academic · Date: 2026-04-07

---

## Executive Summary

This paper is a technically authoritative and historically important treatment of coset codes for band-limited channels, unifying lattice codes and trellis-coded modulation within a single algebraic-geometric framework. However, it requires significant repair at two levels before it is ready for general-academic submission.

**Level 1 — Mechanical (urgent):** The transcription/conversion from the original IEEE typeset source has introduced serious corruption: at least five table cells contain garbled or misplaced data, four instances of `D₈⊥` have been rendered as `D₈¹` or `D₈^{1/8}`, and Table II's header uses undefined symbols. One formula carries a demonstrably wrong subscript that contradicts the paper's own earlier definition. These must be fixed before the paper is readable.

**Level 2 — Repositioning (substantial effort):** The paper is openly framed as an IEEE Transactions invited survey in a multi-part series. The byline, metadata, abstract, introduction, and forward references all presuppose membership in the trellis-coded modulation community. A general-academic submission must be self-contained, neutrally positioned, and accessible to adjacent disciplines. Three rhetorical moves also undermine scholarly credibility: a "folk theorem" stated without proof or lower bound, a key 0.2-dB-per-doubling heuristic with no derivation or citation, and a comparative conclusion ("trellis codes are better") that is not supported by the evidence actually presented.

**Estimated revision effort:** Level 1 (mechanical): 2–4 hours. Level 2 (repositioning): major revision, likely 2–4 weeks.

---

## Basic Language Issues

### Critical — Fix Before Any Submission

**BL-1 · Self-referential lattice comparison (vacuous statement)**
> *"…`Λ_N^M` has a greater or lesser density … than does `Λ_N^M` according to whether `γ(Λ_N)` is greater or less than `γ(Λ_M)`"*

Both sides of the comparison are typeset identically as `Λ_N^M`, making the statement trivially true for every lattice compared with itself. The second occurrence must be `Λ_M^N` (the M-fold Cartesian product of the N-dimensional lattice).
**Fix:** Replace the second `$\Lambda_{N}^{M}$` with `$\Lambda_{M}^{N}$`.

---

**BL-2 · "if and only it" — missing second 'if'**
> *"A mod-2 complex **G**-lattice Λ has depth 1 if and only **it** the code C₁…"*

A one-word omission converts a biconditional into an ungrammatical fragment, obscuring whether this is a sufficient condition, a necessary condition, or both.
**Fix:** Replace `if and only it` with `if and only if`.

---

**BL-3 · Missing `Z` in partition notation `Z²/4²`**
> *"the `Z²/4²` codes ought to be compared to the one-dimensional `Z/4Z` codes"*

`4²` is a scalar; the sublattice must be `4Z²`. The expression is dimensionally inconsistent with every other partition in the paper. Two lines earlier in the same paragraph the correct form `Z²/4Z²` is used.
**Fix:** Replace `$\boldsymbol{Z}^{2}/\boldsymbol{4}^{2}$` with `$\boldsymbol{Z}^{2}/4\boldsymbol{Z}^{2}$`. *(Independently confirmed by both the notation-tracker and formula-cross-checker.)*

---

**BL-4 · Table XI: "Class III codes" text embedded in a `d²_min` data cell**
> `| 16 | Λ₁₆ | RΛ₁₆ | 256 | 4/8 | 2 | Class III codes | 4 | 6.02 | 540 | 2544 | 4.61 |`

A section-divider heading has been absorbed into the `d²_min` column, shifting every subsequent value one column left and making the row unreadable. The formula-checker independently verifies the correct value: `d²_min(RΛ₁₆) = 2 × d²_min(Λ₁₆) = 2 × 8 = 16`, which is consistent with the adjacent `γ = 4` entry (`2^{−2} × 16 = 4`).
**Fix:** Restore `d²_min = 16` in that cell; move "Class III codes" to its own dedicated header row. *(Flagged independently by all three mechanical checkers.)*

---

**BL-5 · Table XI Class III: two rows concatenated into one**
> `| 4 | D₄ | 2D₄  2E₈ | 4 16 | 2/4 | 3/2 | 6 | 3/2^{1/2} | 3.27 | | 46 | |`

The `Λ'` column contains both `2D₄` and `2E₈`; the `2^ν` column contains both `4` and `16`. The D₄/2D₄ and E₈/2E₈ entries have been concatenated into a single row, corrupting all parameter values for both codes.
**Fix:** Split into two rows: (1) `N̄=4, D₄/2D₄, 2^ν=4, k/(k+r)=2/4, ρ=3/2, d²_min=6, γ=3/√2` and (2) `N̄=8, E₈/2E₈, 2^ν=16` with its own parameters (verify against source). *(Flagged by both the basic and notation checkers.)*

---

### Major — Fix Before Submission

| ID | Location | Issue | Fix |
|----|----------|-------|-----|
| BL-6 | Lattice weight-distribution definition | Missing sentence-ending period: `"…ascending order We call this the weight distribution…"` | Insert period after *ascending order* |
| BL-7 | ℝᴺ group description | Stray closing parenthesis: `"…not discrete)."` has one open and two close parens | Delete the trailing `)` |
| BL-8 | Lattice partition geometry | Misspelling: `tesselation` | Replace with `tessellation` |
| BL-9 | RD₄ code formula | Stray comma: `$RD_4 =$, $2\boldsymbol{Z}^4+(4,1,4)$` breaks the equation *(confirmed by notation-tracker)* | Remove comma: `$RD_4 = 2\boldsymbol{Z}^4+(4,1,4)$` |
| BL-10 | Table III, final column | Tilde rendered as minus sign: `−2` instead of `~2`, yielding an impossible negative trellis complexity | Replace `−2` with `~2` |
| BL-11 | Table V / Section VII | Line-break artifact: `Calder-bank-Sloane` | Replace with `Calderbank-Sloane` |
| BL-12 | Barnes-Wall dual identity | Undefined notation `Λ(n)` where `Λ(0,n)` is intended: `Λ(0,n)^⊥ = Λ(n)`. The two-argument form `Λ(r,n)` is used consistently everywhere else; Λ(0,n) is proved self-dual at line 514 *(confirmed by notation-tracker)* | Replace `$\Lambda(n)$` with `$\Lambda(0,n)$` |

### Minor

| ID | Issue | Fix |
|----|-------|-----|
| BL-13 | `onedimensional` in lattice primer | Hyphenate: `one-dimensional` |
| BL-14 | Binomial coefficient written `C_{nj}` and `C_{n_j}` in the same sentence | Standardize to flat subscript `C_{nj}` throughout |
| BL-15 | OCR line-break artifacts in body and References: `fi-nite-dimensional`, `par-tial-unit-memory` | `finite-dimensional`; `partial-unit-memory` |

---

## Notation Issues

**NO-1 · Table II header — three symbols corrupted (Critical)**
> Header row: `| A | k(A) | κ(Λ) | r(Λ) | ρ(Δ) | d²_min(Λ) | γ(Λ) | …`

Three of the first five column labels use garbled forms — plain `A`, `k(A)`, and `ρ(Δ)` — where all should use `Λ`. Neither `A` nor `Δ` is defined anywhere in the paper; this is OCR corruption of the Greek capital `Λ`. All table data (Z², D₄, E₈, …) confirm these are lattice parameters.
**Fix:** Correct the full header to `| Λ | k(Λ) | κ(Λ) | r(Λ) | ρ(Λ) | d²_min(Λ) | γ(Λ) | …` *(Confirmed by both notation-tracker and formula-cross-checker.)*

---

**NO-2 · `D₈⊥` corrupted to `D₈¹` and `D₈^{1/8}` in four table entries (Major)**

The dual checkerboard lattice `D₈⊥` — correctly rendered in running text (line 867) and at lines 894–895 — appears corrupted as `D₈¹` in Table III (line 629) and Table XI (line 1014), and as `D₈^{1/8}` in Tables VII and XI (lines 893, 1008).
**Fix:** Replace all four instances with `$D_8^\perp$`.

---

**NO-3 · Table III uses `‖Λ/Λ'‖` (norm bars) for partition order instead of `|Λ/Λ'|` (cardinality bars) (Major)**

Double bars `‖·‖` denote Euclidean norms throughout the paper (established at line 199). Using them for the cardinality of a quotient group in Table III's header and ratio column introduces a direct semantic conflict with the norm notation.
**Fix:** Replace `\left\|\Lambda/\Lambda'\right\|` with `\left|\Lambda/\Lambda'\right|` in both occurrences in Table III.

---

**NO-4 · Table XI dimension column: `D₁₆/H₁₆` has `N̄ = 8` in Class VI but `N̄ = 16` in Class V (Major)**

`D₁₆` is a 16-dimensional real lattice. The Class V entry correctly gives `N̄ = 16`; the Class VI entry for the same `D₁₆/H₁₆` partition shows `N̄ = 8`. All other Class VI entries use the real dimension consistently.
**Fix:** Change `N̄` to `16` for the Class VI `D₁₆/H₁₆` row.

---

**NO-5 · Variable `n` redefined from "bits per N dimensions" to "`N/2`" within four lines (Minor)**

At line 60, `n` = number of data bits per `N` dimensions. At line 64, `n = N/2` for the sphere-gain formula `G_⊗`. Later, Section III uses `n` again as the Barnes-Wall lattice index. The first two redefinitions are too close together for readability.
**Fix:** Substitute `$m$` or `$\ell$` for `N/2` in the `G_⊗` formula at line 64.

---

**NO-6 · Coset representative vector alternates between bold `c` and non-bold `c` in the same sentence (Minor)**

In the coset definition (line 150): `Λ+c` and `λ+c` use non-bold, but the descriptor phrase uses bold `c`. Since `c` is a vector (an N-tuple), bold is the correct convention per the paper's own usage.
**Fix:** Use `$\boldsymbol{c}$` consistently for the coset representative throughout Section II.B.

---

## Math Verification Issues

**MV-1 · Wrong subscript in coding gain formula — `d²_min(Λ')` should be `d²_min(Λ)` (Critical)**
> *Section IV.B, line 746:* `γ(Λ) = 2^{−ρ(Λ)} d²_min(Λ')`

The prime is wrong. The established definition from Section II.E (line 300) is `γ(Λ) = 2^{−ρ(Λ)} d²_min(Λ)` without a prime. `Λ'` is the *sublattice*, which has strictly larger minimum distance than `Λ`; substituting it into the surrounding argument yields a spurious extra factor `d²_min(Λ')/d²_min(Λ)` and contradicts the correct result `γ(C) = 2^{−ρ(C)} d²_min(C)` derived just three lines earlier (line 728). With the correction, the `d²_min` terms cancel exactly as intended.
**Fix:** Replace `$d_{\text{min}}^{2}(\Lambda')$` with `$d_{\text{min}}^{2}(\Lambda)$` on line 746.

---

**MV-2 · Inconsistent dB rounding for `γ = 2`: `3.02 dB` vs. `3.01 dB` (Minor)**

`10 log₁₀(2) = 3.0103 dB`. The value is rounded to `3.01 dB` consistently in the Introduction (line 78), Section II.E (line 376), Table IV, Table IX, and Table XI. The Discussion section (line 1068) uniquely prints `3.02 dB` for the same quantity.
**Fix:** Change `3.02 dB` to `3.01 dB` at line 1068.

---

## Structure and Logic Issues

**SL-1 · Abstract does not enumerate novel contributions (Major)**

The abstract frames the paper primarily as a unification exercise without distinguishing the paper's own contributions (the geometric-parameter framework, the eight new generic code classes, the comparative classification methodology) from prior work (Ungerboeck, Calderbank–Sloane, Wei). Readers cannot determine what is new.
**Fix:** Add a sentence explicitly enumerating the three novel contributions and distinguishing them from the systematization of prior work.

---

**SL-2 · Section I-C ("Other Coset Codes") disrupts argument flow before framework is established (Major)**

Section I-C introduces generalized non-lattice coset codes before the reader encounters the main lattice framework in Sections II–IV. Section I-D then explicitly states the paper focuses *only* on lattice-type codes. This creates a structural detour: generalities are introduced then immediately abandoned.
**Fix:** Move Section I-C to a short paragraph at the end of Section I-D (or a footnote), explicitly framed as scope-delimiting context rather than substantive content.

---

**SL-3 · "Folk theorem" stated without formal derivation, lower-bound argument, or converse (Major)**
> *"…we propose a folk theorem: it takes two states to get 1.5 dB, four states to get 3 dB, 16 states to get 4.5 dB, perhaps 64 states to get 5.25 dB, and 256 states to get 6 dB…"*

This empirical generalization drives the paper's comparative conclusions but is supported only by informal observation. No lower-bound argument rules out fewer states achieving these gains; the word "perhaps" for the 64-state entry signals the claim is incomplete. Labeling it a "folk theorem" signals lack of proof without explaining whether a proof exists.
**Fix:** Rename as "Empirical Conjecture" and add a sentence acknowledging the absence of a converse bound and identifying this as an open problem. Alternatively, sketch a lower-bound argument from sphere-packing bounds.

---

**SL-4 · Conclusion "trellis codes are better than lattice codes" is contradicted by the surrounding qualifications (Major)**
> *"Trellis codes are better than lattice codes, if we consider effective coding gain versus decoding complexity."*

The three sentences that follow immediately concede: (i) the effective coding gain rule is approximate; (ii) decoding complexity is "highly implementation-dependent"; (iii) no effective coding gain is given for lattice codes because the rule is "questionable" for large error coefficients. The evidence does not support the binary conclusion as stated.
**Fix:** Replace with a qualified observation: *"The evidence suggests trellis codes tend to offer better effective coding gain for a given decoding complexity than lattice codes of comparable fundamental gain, primarily because their error coefficients are much smaller; a rigorous comparison awaits a more precise complexity measure."*

---

**SL-5 · Key rule of thumb (0.2 dB per factor-of-two increase in error coefficient) stated without derivation or citation (Major)**
> *"we will use the rule of thumb that every factor of two increase in the error coefficient reduces the coding gain by about 0.2 dB (at error rates of the order of 10⁻⁶)"*

This heuristic drives the computation of `γ_eff` in Tables V–XI and all comparative conclusions in Section VII. It is introduced without derivation, without a citation, and with only a parenthetical domain-of-validity qualifier. The paper's primary numerical conclusions are materially sensitive to this unanchored input.
**Fix:** Either add a citation to the source or provide a one-paragraph derivation from the Gaussian tail approximation, and explicitly state the error-rate range for which the approximation is valid.

---

**SL-6 · Reading-order prescription in Section I-D is logically contradictory (Minor)**
> *"It is intended that this paper and part II may be read independently … The reader … is advised to skim this paper quickly through Section II, omitting proofs; then to read part II …; and then to return …"*

The paragraph declares the papers independent, then immediately prescribes a preferred reading order spanning both. Conventional outlines describe section contents; they do not prescribe reading strategies.
**Fix:** Condense the reading prescription to a footnote; restore the Outline's function to pure structural description.

---

**SL-7 · Part I / Part II division of labor described in five scattered locations (Minor)**

The relationship between this paper and Part II is referenced in the abstract, Section I-A, Section I-D (twice), Section II, and Section III, without any single location providing a complete, authoritative statement of the division.
**Fix:** Consolidate into one clear paragraph in Section I-D; replace the other five occurrences with a single forward pointer.

---

**SL-8 · Conclusion enumerates ~9 unconnected open problems without prioritization (Minor)**
> *"Suboptimal decoders should be investigated… The design of good sphere packings… The vector quantization problem is dual… The question of multidimensional constellations is not closed."*

No logical ordering, no connection back to the paper's findings, no prioritization. The rhetorical force of the conclusion is diluted.
**Fix:** Lead with the one or two directions most directly motivated by the paper's results; group remaining directions under a "Broader Related Problems" subheading; shorten or cut items not actionable as research directions.

---

## Scholarly Rhetoric Issues

**SR-1 · Abstract presupposes deep familiarity with trellis-coded modulation literature (Major)**

Terms including "lattice partition," "sublattice," "binary encoder," "error coefficient," "constellation expansion factor," and "decoding complexity" appear in the abstract without any glossing. No motivation is offered for readers outside the Ungerboeck/Calderbank–Sloane community.
**Fix:** Add 1–2 opening sentences situating coset codes within algebraic coding theory broadly, and explain why a unified geometric framework is valuable beyond the modulation community.

---

**SR-2 · Introduction is written as insider account for "the modulation community" (Major)**
> *"…it was the trellis-coded modulation schemes of Ungerboeck [8] that captured the attention of the modulation community…"; references to 14.4 kbit/s private-line modems and 9.6 kbit/s switched-network modems.*

A general-academic introduction should orient the reader from a discipline-neutral standpoint and explain the mathematical problem without assuming shared community knowledge.
**Fix:** Open with a paragraph framing the central mathematical question—constructing dense sphere packings achieving near-capacity performance on additive Gaussian channels—without requiring prior knowledge of modem standards.

---

**SR-3 · Technical body calibrated for channel-coding specialists (Major)**
> *"The total coding gain γ_tot(C) is the product of the fundamental coding gain γ(C) with the shape gain γ_s… (γ_s is approximately equal to the ratio of the normalized second moment [7] of an N-cube to that of the region of N-space in which the constellation is contained)."*

The Lattice Primer provides helpful background on lattice theory but leaves communications-engineering terminology (bandwidth-limited channel, SNR, constellation, trellis diagram, normalized second moment) unexplained for a reader from mathematics, statistics, or theoretical computer science.
**Fix:** Expand the introduction or add a "Background and Notation" subsection defining the communications-engineering concepts at the level a mathematician from an adjacent field would need.

---

**SR-4 · Conclusion uses "In the opinion of the author" framing (Minor)**
> *"In the opinion of the author, while many of the best codes may have already been discovered, the fields of coset codes and trellis codes are no further developed than that of ordinary coding theory in the early 1960's."*

This graceful hedge is appropriate for an invited survey but can appear insufficiently rigorous in a research article, where speculative forward-looking claims are expected to be evidence-tied or placed in a clearly labelled "Open Problems" subsection.
**Fix:** Reframe as a short "Open Problems / Future Directions" subsection (see Suggested Rewrites below).

---

## Venue-Style Gap

The paper is openly positioned as an IEEE Transactions on Information Theory **Invited Paper** in a multi-part series. Five structural features are incompatible with general-academic submission conventions:

| # | Feature | Issue | Required Action |
|---|---------|-------|-----------------|
| V-1 | Byline metadata | "G. DAVID FORNEY, JR., FELLOW, IEEE · Invited Paper · IEEE Log Number…" and manuscript receipt date footnote | Remove IEEE credentials, "Invited Paper" label, log number, and manuscript dates |
| V-2 | Series structure | "Part I" in title; all forward references to "Part II in this issue" and prospective "Part III" | Drop "Part I" from title; reframe as self-contained contribution; recategorize Part II as a separate prior/concurrent publication |
| V-3 | Deferred proofs and results | Section III explicitly "summarizes" results from Part II; proofs deferred to companion paper | Either absorb essential results as self-contained lemmas with proofs, or cite Part II as prior published work |
| V-4 | Unpublished references | References [14], [15], [16], [17] listed as "in preparation" or "submitted" (1989) | Update to published versions or remove; move indicative citations to a "Future Work" remark |
| V-5 | Audience calibration | Abstract, introduction, and body all presuppose membership in the trellis-coded modulation community | See SR-1, SR-2, SR-3 above |

---

## Suggested Rewrites

### Abstract (replaces current abstract)
> *Coset codes provide a unified algebraic and geometric framework for constructive coding on band-limited channels. We show that virtually all known good modulation codes—including lattice codes and trellis-coded modulation schemes—can be expressed as coset codes defined by a lattice partition Λ/Λ′ and a binary encoder **C** that selects sequences of cosets. The fundamental parameters governing performance—coding gain, error coefficient, decoding complexity, and constellation expansion—are shown to be purely geometric quantities determined by **C** and Λ/Λ′. We introduce a classification of coset codes into eight generic classes, evaluate their performance within this unified framework, and compare them using a consistent set of performance metrics. Known constructions (Ungerboeck, Calderbank–Sloane, Wei) emerge as special cases; new high-gain classes are identified.*

---

### Introduction opening paragraph (replaces current first paragraph)
> *This paper addresses the problem of constructing efficient codes for band-limited channels with additive Gaussian noise. Shannon's capacity formula implies that simple pulse-amplitude modulation leaves roughly 9 dB of potential coding gain unrealized at practical spectral efficiencies. The goal is to develop constructive coding schemes that recover a substantial fraction of this gap with manageable decoding complexity. We show that nearly all known approaches to this problem—from high-dimensional lattice packings to the trellis-coded modulation of Ungerboeck [8]—share a common algebraic structure that we call a coset code, and that their performance is governed by a small set of geometric invariants.*

---

### Conclusion speculative claim (replaces "In the opinion of the author…")
> *The results presented here suggest the following open problems for future investigation: (1) Are there trellis codes with 64 or fewer states achieving effective coding gain above 5 dB with small error coefficients, or does the empirical conjecture of Section VII admit a formal lower-bound proof? (2) Can suboptimal decoders be systematically designed and analyzed for coset codes? (3) What is the role of ternary and other non-binary coset constructions? (4) Can the geometric framework developed here be extended to channels with memory or to non-Gaussian noise models?*

---

### "Folk theorem" reframing (replaces current "folk theorem" paragraph)
> *Empirical Conjecture: Based on the codes surveyed in Tables V–XI, it appears that two states suffice to achieve 1.5 dB gain, four states for 3 dB, 16 states for 4.5 dB, and 256 states for 6 dB, under the constraint of a reasonably small error coefficient. We do not have a lower-bound argument establishing that fewer states cannot achieve these gains; this is an open problem. The 64-state/5.25-dB entry is particularly uncertain.*

---

## Needs Human Check

The following items require author verification and cannot be resolved by automated review:

1. **Table XI Class III row parameters** (BL-5 / NO-5): After splitting the merged D₄/2D₄ and E₈/2E₈ rows, all numeric parameters for the E₈/2E₈ entry must be verified against the original published paper, as they were corrupted in the current transcription.

2. **References [14]–[17]** (venue finding V-4): The author must determine which of these "in preparation" works were subsequently published and provide updated citation information, or decide which to remove.

3. **The 0.2 dB/factor-of-two rule of thumb** (SL-5): Only the author can confirm whether this rule derives from an unpublished calculation, an earlier paper (possibly [7]), or is truly an original contribution. The appropriate fix (derivation vs. citation) depends on this determination.

4. **State-complexity empirical conjecture** (SL-3): The author must decide whether to claim this as a formal conjecture (implying a belief it is provable) or merely an empirical observation. This affects how the paper positions its contribution relative to capacity/sphere-packing bounds.

5. **Part I / Part II self-containedness** (venue finding V-3): The author must decide which results currently deferred to Part II are essential to this paper's argument and must therefore be incorporated. This requires access to Part II.

6. **Table III approximate complexity values** (BL-10): The `~2` vs `−2` correction assumes the tilde interpretation is correct; the author should verify against the original source.

7. **Section I-C scope** (SL-2): The author should confirm whether phase-modulated and binary block code coset constructions can be omitted from this paper entirely or must be retained for correctness of later claims.

---

## Revision Priorities

### Tier 1 — Must Fix (correctness; paper is misleading or unreadable as-is)

| Priority | Item | Type |
|----------|------|------|
| 1 | MV-1: Wrong subscript `d²_min(Λ')` in coding gain formula (line 746) | Math error |
| 2 | BL-4 + NO-4 (Table XI): "Class III codes" in `d²_min` data cell | Table corruption |
| 3 | BL-5 + NO-5 (Table XI): D₄/2D₄ and E₈/2E₈ rows merged | Table corruption |
| 4 | NO-1 (Table II): `A`, `k(A)`, `ρ(Δ)` → `Λ`, `k(Λ)`, `ρ(Λ)` in header | Notation corruption |
| 5 | NO-2: `D₈¹` / `D₈^{1/8}` → `D₈⊥` in four table entries | Notation corruption |
| 6 | BL-1: Self-referential `Λ_N^M` vs `Λ_N^M` comparison | Logic error |
| 7 | BL-3: `Z²/4²` → `Z²/4Z²` | Math notation |
| 8 | BL-12: `Λ(n)` → `Λ(0,n)` (undefined symbol) | Notation error |

### Tier 2 — Fix Before Submission (mechanical errors that damage credibility)

BL-2 (*if and only if*) · BL-6 (missing period) · BL-7 (stray parenthesis) · BL-8 (*tessellation*) · BL-9 (stray comma in formula) · BL-10 (Table III `~2`) · BL-11 (*Calderbank–Sloane*) · NO-3 (Table III `‖·‖` vs `|·|`) · NO-4 (Table XI `N̄=8` for D₁₆) · MV-2 (3.02→3.01 dB) · BL-13–15 (minor typos and OCR artifacts)

### Tier 3 — Required for General-Academic Positioning (substantial revision)

V-1 through V-5 (remove IEEE venue framing; make paper self-contained) · SR-1 through SR-3 (reframe abstract, introduction, and body for general-academic audience) · SL-5 (anchor the 0.2 dB rule) · SL-3 (reframe folk theorem as conjecture) · SL-4 (qualify trellis-vs-lattice conclusion)

### Tier 4 — Recommended for Scholarly Quality (lower urgency)

SL-1 (enumerate novel contributions in abstract) · SL-2 (move Section I-C) · SL-6 (remove reading-order prescription) · SL-7 (consolidate Part I/II discussion) · SL-8 (prioritize conclusion open problems) · SR-4 (reframe first-person conclusion) · NO-5 (rename `n=N/2`) · NO-6 (bold coset vector consistently)
