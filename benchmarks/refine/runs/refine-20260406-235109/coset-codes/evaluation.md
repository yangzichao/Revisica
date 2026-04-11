# Refine Benchmark: coset-codes

- Paper: `/Users/zichaoyang/workplace/ReviseAgent/benchmarks/refine_cases/coset-codes.md`
- Expected comments: 19
- Our findings: 44
- Recall (matched + partial): 63.2%
- Full recall (matched only): 21.1%

## Expected vs Found

### [~] PARTIAL: Decoding complexity as a geometric parameter

- **Refine score:** 0.05
- **Match confidence:** 0.36
- **Explanation:** Heuristic score: 0.36
- **Expected quote:** The fundamental coding gain of a coset code, as well as other important parameters such as the error coefficient, the decoding complexity, and the constellation expansion factor, are purely geometric ...
- **Matched findings (1):**
  - [structure] Assertion 'trellis codes are better than lattice codes' is unsupported by the evidence presented

### [X] MISSED: Definition of fundamental volume and redundancy in the Introduction

- **Refine score:** 0.09
- **Match confidence:** 0.00
- **Explanation:** Heuristic score: 0.00
- **Expected quote:** The fundamental coding gain of the coset code is denoted by $\gamma(\mathbb{C})$ and is defined by two elementary geometrical parameters: the minimum squared distance $d_{\text {min }}^{2}(\mathbb{C})...

### [~] PARTIAL: Role of algebraic structure in the coset code framework

- **Refine score:** 0.09
- **Match confidence:** 0.45
- **Explanation:** Heuristic score: 0.45
- **Expected quote:** In general, these code constructions rely very little on the linearity properties of the groups (e.g., lattices, sublattices) on which they are based, and the codes so constructed are often not linear...
- **Matched findings (3):**
  - [venue] Abstract assumes deep prior familiarity with trellis-coded modulation literature, excluding general-academic readers
  - [structure] Abstract does not explicitly enumerate paper's novel contributions
  - [structure] Section I-C ('Other Coset Codes') disrupts argument flow before framework is established

### [X] MISSED: Mismatch in coset decomposition formulas

- **Refine score:** 0.05
- **Match confidence:** 0.00
- **Explanation:** Heuristic score: 0.00
- **Expected quote:** A partition chain induces a multiterm coset decomposition chain, with a term corresponding to each partition; e.g., if $\Lambda / \Lambda^{\prime} / \Lambda^{\prime \prime}$ is a partition chain, then...

### [X] MISSED: Description of coset representatives in Sec. II.F

- **Refine score:** 0.09
- **Match confidence:** 0.00
- **Explanation:** Heuristic score: 0.00
- **Expected quote:** Thus the $2^{K}$ binary linear combinations $\left\{\sum a_{k} \boldsymbol{g}_{k}\right\}$ of the generators $\boldsymbol{g}_{k}$ are a system of coset representatives $\left[\Lambda_{k} / \Lambda_{k+...

### [~] PARTIAL: Clarity of argument for mod-4 lattice structure

- **Refine score:** 0.23
- **Match confidence:** 0.28
- **Explanation:** Heuristic score: 0.28
- **Expected quote:** For a further refinement, let $\Lambda_{e}$ be the set of all points in $\Lambda$ whose coordinates are all even. Then $\Lambda_{e}$ is a lattice, a sublattice of $\Lambda$, with $\boldsymbol{4} \bold...
- **Matched findings (3):**
  - [venue] Multi-part series structure with forward references to companion papers is incompatible with a standalone general-academic submission
  - [notation-tracker] Table II header uses three different symbols for the same lattice argument
  - [notation-tracker] Dual lattice $\Lambda(0,n)^\perp$ equated to undefined notation $\Lambda(n)$

### [+] MATCHED: Undefined notation for the dual of a Barnes-Wall lattice

- **Refine score:** 0.23
- **Match confidence:** 0.75
- **Explanation:** Heuristic score: 0.75
- **Expected quote:** Thus $\Lambda(n, n)^{\perp}=\boldsymbol{G}^{N} \simeq \boldsymbol{Z}^{2 N}, \Lambda(0, n)^{\perp}= \Lambda(n)$, and $\Lambda(n-1, n)^{\perp}, n \geq 1$, is the dual $D_{N}^{\perp}$ of the checkerboard...
- **Matched findings (3):**
  - [venue] Technical exposition calibrated for channel-coding specialists, not a general-academic reader
  - [basic] Missing 'Z²' in lattice-partition notation 'Z²/4²'
  - [basic] Undefined notation 'Λ(n)' used where 'Λ(0,n)' is expected

### [+] MATCHED: Notation for a lattice in Table III

- **Refine score:** 0.09
- **Match confidence:** 0.70
- **Explanation:** Heuristic score: 0.70
- **Expected quote:** TABLE III
Useful Lattice Partitions
| Λ | $\Lambda^{\prime}$ | $2 N$ | $\left\|\Lambda / \Lambda^{\prime}\right\|$ | $\mu$ | $\kappa$ | $\rho$ | $d_{\text {min }}^{2}(\Lambda)$ | $d_{\text {min }}^{2}...
- **Matched findings (3):**
  - [venue] Technical exposition calibrated for channel-coding specialists, not a general-academic reader
  - [structure] Table XI embeds class-break labels inside data cells, creating ambiguous row attribution
  - [basic] Missing 'Z²' in lattice-partition notation 'Z²/4²'

### [X] MISSED: Description of the Ungerboeck encoder in Sec. IV.A

- **Refine score:** 0.05
- **Match confidence:** 0.00
- **Explanation:** Heuristic score: 0.00
- **Expected quote:** For example, the four-state Ungerboeck code shown in Figs. 2 and 3 uses the four-state rate-1/2 convolutional code whose encoder and trellis diagram are illustrated in Fig. 10. Contrary to convention,...

### [+] MATCHED: Incorrect formula for lattice coding gain

- **Refine score:** 0.05
- **Match confidence:** 0.59
- **Explanation:** Heuristic score: 0.59
- **Expected quote:** Relative to $\gamma(\Lambda)=2^{-\rho(\Lambda)} d_{\text {min }}^{2}\left(\Lambda^{\prime}\right)$, the gain $\gamma(\mathbb{C})$ is greater by the distance gain factor of $d_{\text {min }}^{2}(\mathb...
- **Matched findings (3):**
  - [venue] Abstract assumes deep prior familiarity with trellis-coded modulation literature, excluding general-academic readers
  - [venue] Technical exposition calibrated for channel-coding specialists, not a general-academic reader
  - [structure] Abstract does not explicitly enumerate paper's novel contributions

### [~] PARTIAL: Incomplete premise in Lemma 6

- **Refine score:** 0.05
- **Match confidence:** 0.27
- **Explanation:** Heuristic score: 0.27
- **Expected quote:** Lemma 6: If $\Lambda^{\prime}$ is a mod-2 lattice, $C$ is a $2^{\nu}$-state, rate- $k /(k+r)$ convolutional code and the labeling map $\boldsymbol{c}(\boldsymbol{a})$ is linear modulo $\Lambda^{\prime...
- **Matched findings (1):**
  - [basic] Missing word 'if' in 'if and only it'

### [~] PARTIAL: Inconsistency in Decoding Complexity Calculation

- **Refine score:** 0.5
- **Match confidence:** 0.36
- **Explanation:** Heuristic score: 0.36
- **Expected quote:** N_{D} is the number of decoding operations using the trellis-based decoding algorithms of the partition \Lambda / \Lambda^{\prime} whose complexity is given in Table III, followed by a conventional Vi...
- **Matched findings (1):**
  - [structure] Assertion 'trellis codes are better than lattice codes' is unsupported by the evidence presented

### [X] MISSED: Unclear reference to "last three codes"

- **Refine score:** 0.0
- **Match confidence:** 0.00
- **Explanation:** Heuristic score: 0.00
- **Expected quote:** They also consider the following: Ungerboeck-type codes based on partitions $\boldsymbol{Z} / \mathbf{4} \boldsymbol{Z}, \boldsymbol{Z}^{2} / 2 \boldsymbol{Z}^{2}$ and $\boldsymbol{Z}^{2} / 2 R \bolds...

### [~] PARTIAL: Inconsistent encoder description for Class II codes

- **Refine score:** 0.09
- **Match confidence:** 0.39
- **Explanation:** Heuristic score: 0.39
- **Expected quote:** Let $\Lambda / \Lambda^{\prime}$ again be a $2^{2 k}$-way lattice partition with $d_{\text {min }}^{2}\left(\Lambda^{\prime}\right)=2 d_{\text {min }}^{2}(\Lambda)$. Let $C$ be a rate- $1 / 2,2^{2 k}$...
- **Matched findings (3):**
  - [venue] Several references are 'in preparation' or 'submitted', inconsistent with archival expectations of a general-academic submission
  - [structure] Table XI embeds class-break labels inside data cells, creating ambiguous row attribution
  - [basic] Table XI row: literal string 'Class III codes' appears in the d²_min data column

### [~] PARTIAL: Path enumeration for Class V error coefficient

- **Refine score:** 0.23
- **Match confidence:** 0.27
- **Explanation:** Heuristic score: 0.27
- **Expected quote:** The coefficient of $N_{\Lambda}^{2}$ follows from the observation that in the code trellis, starting from a given zero state and ending at some later zero state, there are $2^{k}-1$ nonzero paths of l...
- **Matched findings (3):**
  - [structure] 'Folk theorem' stated without formal derivation, citation, or converse argument
  - [structure] Central 'effective coding gain' rule of thumb introduced without derivation or citation
  - [basic] Spurious mid-word hyphen: 'Calder-bank-Sloane'

### [+] MATCHED: Minimum distance argument for Class VI codes

- **Refine score:** 1.0
- **Match confidence:** 0.53
- **Explanation:** Heuristic score: 0.53
- **Expected quote:** Furthermore, it ensures that if the input sequence has a finite number of nonzero $\boldsymbol{x}_{t}$, then the encoder outputs are nonzero at at least three different times: once when the sequence b...
- **Matched findings (3):**
  - [venue] Multi-part series structure with forward references to companion papers is incompatible with a standalone general-academic submission
  - [structure] Section I-C ('Other Coset Codes') disrupts argument flow before framework is established
  - [structure] Table XI embeds class-break labels inside data cells, creating ambiguous row attribution

### [X] MISSED: Parameter mismatch for lattice X_32 in Discussion

- **Refine score:** 0.09
- **Match confidence:** 0.00
- **Explanation:** Heuristic score: 0.00
- **Expected quote:** Note also that the lattices $X_{24}$ and $X_{32}$ achieve $\gamma=2^{3 / 2}(4.52 \mathrm{~dB})$ and $\gamma=2^{13 / 8}(4.89 \mathrm{~dB})$ with 8 and 16 states, respectively, but with $\mu=2, \rho=1 /...

### [X] MISSED: Incorrect example for γ=3 codes in Discussion

- **Refine score:** 0.18
- **Match confidence:** 0.00
- **Explanation:** Heuristic score: 0.00
- **Expected quote:** There is a nearby cluster of codes that achieve $\gamma=3$ ( 4.77 dB ), with either $\mu=3, \rho=1$ and $d_{\min }^{2}=6$, or $\mu=4$, $\rho=2$ and $d_{\text {min }}^{2}=12$; e.g., the 16- and 32-stat...

### [~] PARTIAL: Parameter comparison between Wei code and X24 lattice

- **Refine score:** 0.05
- **Match confidence:** 0.30
- **Explanation:** Heuristic score: 0.30
- **Expected quote:** Of all the codes we have considered, a few stand out as "special." The four-state two-dimensional Ungerboeck code is certainly in this category because it is the unique code with $\gamma=2$ and $\tild...
- **Matched findings (1):**
  - [structure] Abstract does not explicitly enumerate paper's novel contributions

