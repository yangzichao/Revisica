# Executive Summary
Writing-review adjudication failed. This fallback report preserves raw role outputs.

## Basic Language Issues

See raw role outputs below.

## Structure and Logic Issues

See raw role outputs below.

## Scholarly Rhetoric Issues

See raw role outputs below.

## Venue-Style Gap

Target profile: `general-academic`.

## Suggested Rewrites

Inspect raw role outputs for rewrite suggestions.

## Needs Human Check

The final judge did not complete successfully.

## Revision Priorities

1. Inspect raw role outputs below.

## Raw Role Outputs

### structure from claude:sonnet

```json
[
  {
    "category": "structure_logic",
    "severity": "major",
    "title": "Introduction conflates model exposition and literature context, disrupting logical flow",
    "snippet": "We now lay out the elements of the model in more detail. Individuals play a simultaneous-move game... [three full paragraphs of model detail] ... We now place the paper in the context of the literature.",
    "explanation": "The Introduction devotes three consecutive paragraphs (paragraphs 2\u20134) to a detailed technical walkthrough of the model\u2014including the payoff structure, the planner's budget constraint, and the mechanics of strategic complements versus substitutes\u2014before pivoting to the literature review at paragraph 7. This inverts the conventional logic of an economics introduction (motivation \u2192 contribution \u2192 related work \u2192 roadmap). The contribution framing arrives too late and too briefly to anchor the preceding technical detail.",
    "fix": "Condense paragraphs 2\u20134 of the Introduction to a high-level description of the model primitives (one paragraph). Move the principal-component mechanism sketch directly after the motivation statement. Bring the literature review and contribution claim forward to immediately follow the motivation, before the technical roadmap paragraph."
  },
  {
    "category": "contribution_framing",
    "severity": "major",
    "title": "Contribution statement is vague and self-deprecating relative to the paper's substantive results",
    "snippet": "The main contribution of this paper is methodological. It lies in (i) using the principal components approach to decompose the effect of an intervention on social welfare and (ii) using the structure afforded by this decomposition to characterize optimal interventions.",
    "explanation": "The contribution statement restricts itself to methodology and describes the approach in purely procedural terms. It does not assert what the paper discovers\u2014namely, the directional complementarity between strategic spillover type and eigenvector order, the budget-threshold condition for simplicity, the spectral-gap interpretation for network topology, and the extension to stochastic environments. Framing a contribution purely as a technique without stating the substantive insights that technique generates weakens the paper's claim to the reader.",
    "fix": "Expand the contribution statement to enumerate substantive discoveries: (1) under strategic complements, eigenvector centrality (top principal component) is welfare-maximizing for large budgets; (2) under strategic substitutes, the bottom principal component encoding the optimal bipartition drives targeting; (3) simplicity of optimal interventions is governed by the spectral gap, linking network cohesion/divisibility directly to policy design. The methodological claim can follow as the unifying mechanism."
  },
  {
    "category": "claim_evidence_gap",
    "severity": "major",
    "title": "Intuition for Corollary 1 (ordering of similarity ratios) is deferred but never fully supplied",
    "snippet": "Corollary 1: Suppose Assumptions 1-3 hold and the network game satisfies Property A. If the game is one of strategic complements (\u03b2>0), then |r*_\u2113| is decreasing in \u2113; if the game is one of strategic substitutes (\u03b2<0), then |r*_\u2113| is increasing in \u2113.",
    "explanation": "Corollary 1 is stated with only a brief bridge sentence as transition. There is no dedicated paragraph explaining why \u03b1_\u2113 is larger for smaller \u2113 when \u03b2>0 and larger for larger \u2113 when \u03b2<0, nor why this ranking translates into the welfare-relevant targeting direction. The intuition promised in the Introduction\u2014that top eigenvectors capture global structure and bottom eigenvectors capture local structure\u2014is never formally connected to Corollary 1 in Section 4.",
    "fix": "After stating Corollary 1, add a two-to-three sentence paragraph explaining: (a) \u03b1_\u2113 = (1\u2212\u03b2\u03bb_\u2113)^{\u22122} is monotone in \u03bb_\u2113 with direction depending on the sign of \u03b2; (b) higher \u03b1_\u2113 means a marginal investment in that direction yields higher welfare return; (c) therefore the planner concentrates spending on the direction with the highest return per unit of budget, which for \u03b2>0 is the top eigenvector (global structure) and for \u03b2<0 is the bottom eigenvector (bipartition structure). This makes the verbal Introduction claims verifiable from within Section 4."
  },
  {
    "category": "structure_logic",
    "severity": "minor",
    "title": "Section 3 header and opening paragraph overstate the section's scope",
    "snippet": "This section introduces a basis for the space of standalone marginal returns and actions in which, under our assumptions on G, strategic effects and the planner's objective both take a simple form.",
    "explanation": "The claim that the planner's objective 'takes a simple form' in this basis is only fully established in Section 4 when Theorem 1 is derived. Section 3 itself only shows that equilibrium actions decouple in this basis and defines cosine similarity. The section title 'PRINCIPAL COMPONENTS' is underspecified for the game-theoretic application being developed.",
    "fix": "Revise the opening sentence to restrict scope to what is established within the section: 'This section introduces the principal components of G\u2014a basis in which strategic effects decouple across components, simplifying the equilibrium characterization and preparing the analysis of optimal interventions in Section 4.' Rename the section to 'PRINCIPAL COMPONENT DECOMPOSITION OF THE GAME' or equivalent."
  },
  {
    "category": "scholarly_rhetoric",
    "severity": "minor",
    "title": "Meta-announcement 'We now place the paper in the context of the literature' is mechanical and disrupts flow",
    "snippet": "We now place the paper in the context of the literature. The intervention problem we study concerns optimal policy in the presence of externalities. Research over the past two decades has deepened our understanding...",
    "explanation": "The sentence functions as a section label rather than a rhetorical move. This phrasing forces the literature discussion into a single paragraph at the end of the Introduction, making it feel like an afterthought. The literature review is also extremely compressed and relies heavily on footnotes, fragmenting the narrative.",
    "fix": "Remove the meta-announcement sentence. Integrate the literature motivation earlier in the Introduction after the first paragraph with a natural transition: 'A growing literature has studied how network structure shapes equilibrium behavior [citations], creating demand for policy frameworks that exploit this structure. Our approach addresses this demand by\u2026' Reserve the end-of-introduction paragraph for summarizing how this paper's contribution differs from the closest antecedents."
  },
  {
    "category": "structure_logic",
    "severity": "minor",
    "title": "Section 5 (Incomplete Information) is structurally disconnected from the large-budget simplicity results of Section 4",
    "snippet": "In the basic model, we assumed that the planner knows the standalone marginal returns of every individual. This section extends the analysis to settings where the planner does not know these parameters.",
    "explanation": "The transition from Section 4 does not motivate why a planner would face incomplete information after the detailed deterministic analysis. The connection to the large-budget simplicity result is particularly important\u2014Proposition 3 exactly recovers the deterministic result with the expected status quo\u2014but this connection is not explicitly drawn. The section reads as an isolated extension rather than a deepening of the paper's main theme.",
    "fix": "Add a transitional sentence at the start of Section 5: 'The simplicity of large-budget interventions\u2014where the planner need only know the relevant eigenvector of G\u2014motivates the question of how much information about individual standalone marginal returns is actually needed. We now show that the qualitative ordering of principal components extends to settings where the planner knows only the distribution of these returns.' This frames incomplete information as testing the robustness of Section 4's insights."
  },
  {
    "category": "claim_evidence_gap",
    "severity": "minor",
    "title": "Claim that Property A 'is not essential' is asserted without guidance on which results survive the relaxation",
    "snippet": "While Property A facilitates analysis, it is not essential. Supplemental Material Section OA3.1 extends the analysis to cover important cases where this property does not hold.",
    "explanation": "The paper asserts this critical assumption can be relaxed but gives no indication of whether the main qualitative insights\u2014the ordering of principal components by strategic type, the spectral-gap condition for simplicity\u2014survive. Pointing readers to the Supplemental Material without any preview of what survives or fails is insufficient for an assumption that underpins every main result in Sections 4 and 5.",
    "fix": "Add one sentence summarizing the key finding from OA3.1: e.g., 'In Section OA3.1, we show that the principal-component ordering of Corollary 1 extends to a broader class of externality structures, though the explicit proportionality formula of Theorem 1 requires modification.' This confirms the conceptual contribution is robust without requiring a detour to the supplement."
  },
  {
    "category": "scholarly_rhetoric",
    "severity": "minor",
    "title": "Conclusion refers to 'ongoing work' that by the 2020 date may now be published, undermining credibility",
    "snippet": "In ongoing work, Galeotti, Golub, Goyal, Talam\u00e0s, and Tamuz (2020) show that the principal component approach that we employed in this paper is useful in deriving the optimal taxation scheme...",
    "explanation": "The phrase 'ongoing work' refers to a 2020 manuscript. Depending on publication timing, this work may no longer be 'ongoing' and may have appeared in print or as a finalized working paper. More broadly, the two forward-looking directions mentioned in the conclusion are each dispatched in one sentence without explaining tractability or expected difficulty, making them appear perfunctory.",
    "fix": "Update the reference to Galeotti et al. (2020) with actual publication status. If published, cite it normally and describe the result as established. Expand the second future direction (interventions on the interaction matrix) with one sentence explaining what makes it a technically distinct but natural open question."
  }
]
```

### venue from claude:sonnet

```json
[
  {
    "category": "abstract_positioning",
    "severity": "critical",
    "title": "Abstract assumes specialist vocabulary without grounding",
    "snippet": "We analyze this question by decomposing any intervention into orthogonal principal components, which are determined by the network and are ordered according to their associated eigenvalues. There is a close connection between the nature of spillovers and the representation of various principal components in the optimal intervention.",
    "explanation": "The abstract deploys terms like 'orthogonal principal components', 'eigenvalues', 'strategic complements/substitutes', and 'standalone marginal returns' without any lay grounding. For a general-academic venue, the abstract is the primary filter for cross-disciplinary readers deciding whether to engage. These terms are interpretable within economics and applied mathematics but not in sociology, public health, or political science without explanation. The abstract also states the methodological contribution before articulating the substantive, real-world problem motivating the work \u2014 the reverse of what general-academic framing requires.",
    "fix": "Restructure the abstract to open with the applied problem (how should a policy-maker allocate limited resources to change behavior in a network?), state in plain language what the main insight is (the right targeting strategy depends on whether behaviors reinforce or crowd out each other, and on global vs. local network structure), and then briefly name the mathematical technique. Defer eigenvalue terminology to the body.",
    "rewrite": "We study how a planner with a limited budget should target individuals in a network to maximize collective welfare. Agents influence each other's incentives through network links, and these spillovers can amplify or dampen each other depending on whether behaviors are strategic complements or substitutes. We show that the optimal intervention has a clean structure: it can be decomposed along the network's principal directions (eigenvectors), and the nature of strategic interaction determines which directions should receive the most weight. When behaviors reinforce each other, the planner should concentrate resources on globally central individuals; when behaviors crowd each other out, resources should be distributed to create local contrast between neighbors. With large budgets, optimal interventions simplify to targeting a single network direction, with the required budget determined by the network's spectral gap."
  },
  {
    "category": "introduction_positioning",
    "severity": "critical",
    "title": "Introduction launches into model mechanics before establishing the applied stakes",
    "snippet": "We now lay out the elements of the model in more detail. Individuals play a simultaneous-move game with continuous actions. An agent's action creates standalone returns for that agent independent of anyone else's action, but it also creates spillovers.",
    "explanation": "The second paragraph of the introduction immediately pivots to laying out formal model mechanics ('simultaneous-move game', 'standalone marginal returns', 'separable' cost functions) rather than first making a persuasive case for why the targeting problem matters, who faces it in practice, and what existing approaches fail to deliver. A general-academic reader from sociology, epidemiology, or computer science will disengage before the intellectual contribution is clear. The introduction does not situate the problem in concrete empirical or policy contexts until deep in the model description.",
    "fix": "Devote the first two to three paragraphs of the introduction to: (1) a vivid, concrete motivating scenario (e.g., a public health authority deciding which nodes in a contact network to target with an intervention, or a firm deciding which workers to train); (2) why naive approaches (target the highest-degree nodes, target randomly) fall short; and (3) the paper's punchline in plain language. Only then introduce the formal model elements.",
    "rewrite": "Consider a public health authority seeking to encourage vaccination or a development organization aiming to boost agricultural investment in a village network. The authority has a limited budget and must decide which individuals to target with information, subsidies, or encouragement. Neighbors influence each other: when one farmer invests, it raises or lowers incentives for adjacent farmers depending on whether investments are complementary or substitutable. Targeting the most connected individuals is a natural heuristic, but it is not always optimal \u2014 the right answer depends on the structure of strategic interaction. This paper provides a principled characterization of optimal targeting that accounts for both network structure and the direction of strategic spillovers."
  },
  {
    "category": "audience_positioning",
    "severity": "major",
    "title": "Literature review is positioned exclusively toward economics specialists",
    "snippet": "Research over the past two decades has deepened our understanding of the empirical structure of networks and the theory of how networks affect strategic behavior. This has led to the study of how policy design should incorporate information about networks. Network interventions are currently an active subject of research not only in economics but also in related disciplines such as computer science, sociology, and public health.",
    "explanation": "Although the paper acknowledges cross-disciplinary interest, the literature discussion remains entirely within economics citations. For a general-academic venue, this is a missed opportunity: readers from other fields will not see their own literature reflected, and the claim of multi-disciplinary relevance reads as a perfunctory gesture rather than a genuine bridge. The paper does not cite or engage with the diffusion/seeding literature in CS (Kempe et al.), peer-effects literature in sociology, or contact-tracing/immunization targeting in epidemiology.",
    "fix": "Expand the literature review to explicitly cite and contrast with parallel work in other disciplines, explaining in accessible language what each discipline has contributed and how this paper complements or extends those contributions. Integrate citations from network diffusion (CS), social influence (sociology), and immunization/seeding (public health) alongside the economics references."
  },
  {
    "category": "venue_alignment",
    "severity": "major",
    "title": "Theorem-proof format without intuitive scaffolding is misaligned with general-academic expectations",
    "snippet": "Theorem 1: Suppose Assumptions 1-3 hold and the network game satisfies Property A. At the optimal intervention, the cosine similarity between y* and principal component u^\u2113(G) satisfies the following proportionality...",
    "explanation": "General-academic venues typically expect results to be presented with their substantive interpretation as the primary communication, with formal statements serving supporting precision \u2014 not as the organizing structure of exposition. The paper's theorems are stated and then followed by proof sketches and then interpretation. In a general-academic venue, this ordering is reversed: intuition and applied takeaway should come first, the formal result should serve as precision, and proof sketches should be clearly labeled as optional for specialist readers.",
    "fix": "Reorganize Section 4 to lead each result with a plain-language statement of what will be shown and why it matters. Present the formal theorem as a boxed precision statement following the verbal description. Move proof sketches to remarks or footnotes, with a pointer to the appendix. Use figures (Figure 2, Figure 3) earlier and more prominently to anchor intuition before formalism."
  },
  {
    "category": "venue_alignment",
    "severity": "major",
    "title": "Contribution framing as 'methodological' undersells relevance to a general audience",
    "snippet": "The main contribution of this paper is methodological. It lies in (i) using the principal components approach to decompose the effect of an intervention on social welfare and (ii) using the structure afforded by this decomposition to characterize optimal interventions.",
    "explanation": "Framing the paper's contribution as 'methodological' is common and appropriate in top economics theory journals, where methodological tools are valued as independent contributions. However, in a general-academic venue, 'methodological' is often read as meaning 'of limited substantive interest' or 'not empirical.' General readers expect the framing to foreground substantive insights and policy implications, with methodological innovation as a means to those ends.",
    "fix": "Reframe the contribution around the substantive insight \u2014 that the strategic structure of interaction (complements vs. substitutes) is the key determinant of which network positions should be targeted \u2014 with the principal-component method described as the analytical tool that reveals this insight. Emphasize how the results apply to concrete policy design across domains.",
    "rewrite": "This paper shows that the right way to target individuals in a network depends crucially on whether their behaviors reinforce or crowd out each other. When behaviors are strategic complements, optimal targeting concentrates on globally central (high eigenvector centrality) nodes; when they are strategic substitutes, the planner should instead create deliberate local contrasts \u2014 boosting some neighbors and reducing others. These insights are derived using a principal-component decomposition of the network, which provides a tractable and generalizable method for policy design under network spillovers."
  },
  {
    "category": "audience_positioning",
    "severity": "major",
    "title": "Applied examples appear after dense formalism rather than before it",
    "snippet": "We present two economic applications to illustrate the scope of our model. The first example is a classical investment game, and the second is a game of providing a local public good.",
    "explanation": "Examples 1 (investment game) and 2 (local public goods) appear in Section 2 after the full formal model is introduced, and are presented as formal special cases rather than as motivating contexts that build reader understanding. For a general-academic audience, examples should arrive early \u2014 ideally before or alongside the formal model \u2014 and be described in non-technical language first, with the formal connection made clear afterward.",
    "fix": "Move at least one concrete example to the introduction, described entirely in plain language before the formal model begins. Retain the formal example treatment in Section 2, but add a connecting sentence reminding readers which example they are now formalizing. Consider adding a third example from a non-economics domain (e.g., disease prevention, information diffusion) to signal genuine cross-disciplinary relevance."
  },
  {
    "category": "rewrite_suggestion",
    "severity": "minor",
    "title": "Roadmap paragraph is purely structural and does not guide general readers",
    "snippet": "The rest of the paper is organized as follows. Section 2 presents the optimal intervention problem. Section 3 sets out how we apply a principal component decomposition to our game. Section 4 characterizes optimal interventions. Section 5 studies a setting where the planner has incomplete information about agents' standalone marginal returns. Section 6 concludes.",
    "explanation": "The roadmap lists section numbers and topics with no indication of which sections are essential for general readers, which contain technical details that can be skimmed, or what the logical thread connecting the sections is. For a general-academic audience, a roadmap should guide readers with different backgrounds through the paper.",
    "fix": "Rewrite the roadmap to signal the logical progression and explicitly indicate which sections carry the main insight vs. which are specialist extensions. Add one sentence on what each section contributes to the overall argument, not just what it covers.",
    "rewrite": "The paper proceeds as follows. Section 2 introduces the model; readers primarily interested in the results may focus on the two motivating examples (Examples 1 and 2) and return for details as needed. Section 3 develops the principal-component framework that underpins all subsequent results \u2014 it is mathematically self-contained and accessible to readers familiar with linear algebra. Section 4 presents the main results on optimal interventions. Section 5 extends the analysis to settings where the planner has incomplete information, and can be read independently of Section 4's technical details. Section 6 concludes."
  },
  {
    "category": "rewrite_suggestion",
    "severity": "minor",
    "title": "Conclusion does not articulate broader implications or limitations for non-specialist readers",
    "snippet": "We have studied the problem of a planner who seeks to optimally target incentive changes in a network game... To develop these ideas in the simplest way, we have focused on a model in which the matrix of interaction is symmetric, the costs of intervention are quadratic, and the intervention itself takes the form of altering the standalone marginal returns of actions.",
    "explanation": "The conclusion honestly lists the model's restrictions (symmetry, quadratic costs, marginal-return interventions) but misses the chance to articulate broader implications across domains or discuss what empirical work would be needed to apply the results in practice. The current conclusion is well-suited for an economics journal but does not broaden the paper's reach to a general-academic audience.",
    "fix": "Add one paragraph that explicitly discusses applicability to non-economics settings (public health, organizational behavior, platform design), identifies what data or empirical parameters a practitioner would need to apply the results, and states the key assumption whose violation would most seriously limit the approach (e.g., the symmetry assumption, or the assumption that the planner can observe the network)."
  },
  {
    "category": "venue_alignment",
    "severity": "minor",
    "title": "Generic masculine pronoun ('his') for agents is inconsistent with general-academic norms",
    "snippet": "For example, suppose the planner increases a given individual's standalone marginal returns to effort, thereby increasing his effort.",
    "explanation": "The paper uses 'his' as the default pronoun for a generic individual. Generic use of 'his' for agents is inconsistent with current style norms in general-academic venues, which prefer gender-neutral constructions ('their', 'the individual's') or consistent inclusive language.",
    "fix": "Replace all instances of 'his' used generically for network agents with 'their' or rephrase to avoid the pronoun. Apply consistent gender-neutral language throughout.",
    "rewrite": "For example, suppose the planner increases a given individual's standalone marginal returns to effort, thereby increasing their effort."
  }
]
```

### basic from claude:sonnet

```json
[
  {
    "category": "typo",
    "severity": "critical",
    "title": "Circular change-of-variables formula \u2014 missing tilde on b_i",
    "snippet": "Performing the change of variables $b_{i}=\\left[\\tau-b_{i}\\right] / 2$ and $\\beta=-\\tilde{\\beta} / 2$ (with the status quo equal to $\\hat{b}_{i}=\\left[\\tau-\\tilde{b}_{i}\\right] / 2$ )",
    "explanation": "The formula $b_i = [\\tau - b_i]/2$ defines $b_i$ circularly in terms of itself, yielding $3b_i = \\tau$ \u2014 a contradiction with the intended substitution. The companion status quo formula correctly uses $\\tilde{b}_i$ (the original public-goods parameter). The change-of-variables formula should also use $\\tilde{b}_i$.",
    "fix": "Change $b_{i}=\\left[\\tau-b_{i}\\right] / 2$ to $b_{i}=\\left[\\tau-\\tilde{b}_{i}\\right] / 2$."
  },
  {
    "category": "typo",
    "severity": "major",
    "title": "Missing possessive 's' \u2014 \"individual'\" instead of \"individuals'\"",
    "snippet": "the vector of individual' eigenvector centralities in the",
    "explanation": "The apostrophe-s is missing from the plural possessive 'individuals''. The phrase describes centralities belonging to multiple individuals, so it should be \"individuals'\".",
    "fix": "Change \"individual' eigenvector centralities\" to \"individuals' eigenvector centralities\"."
  },
  {
    "category": "clarity",
    "severity": "major",
    "title": "Cosine similarity definition missing \u2016z\u2016 in denominator",
    "snippet": "The cosine similarity of two nonzero vectors $\\boldsymbol{y}$ and $\\boldsymbol{z}$ is $\\rho(\\boldsymbol{y}, \\boldsymbol{z})=\\frac{\\boldsymbol{y} \\cdot \\boldsymbol{z}}{\\|\\boldsymbol{y}\\|}$.",
    "explanation": "The standard cosine similarity is $\\frac{\\boldsymbol{y}\\cdot\\boldsymbol{z}}{\\|\\boldsymbol{y}\\|\\|\\boldsymbol{z}\\|}$. The denominator as written omits $\\|\\boldsymbol{z}\\|$. Although every application in the paper pairs $\\boldsymbol{y}$ with a unit-norm eigenvector (so $\\|\\boldsymbol{z}\\|=1$ and the formula holds numerically), the stated definition is non-standard and will confuse readers. The proof in the Appendix (equation 12) also expands the denominator as $\\|\\boldsymbol{y}^*\\|\\|\\boldsymbol{u}^\\ell(\\boldsymbol{G})\\|$, confirming the full formula is intended.",
    "fix": "Change the definition to $\\rho(\\boldsymbol{y}, \\boldsymbol{z})=\\frac{\\boldsymbol{y} \\cdot \\boldsymbol{z}}{\\|\\boldsymbol{y}\\|\\|\\boldsymbol{z}\\|}$."
  },
  {
    "category": "reference_ambiguity",
    "severity": "major",
    "title": "\"Status quo actions\" incorrectly labels $\\hat{\\boldsymbol{b}}$ (standalone marginal returns)",
    "snippet": "As long as the status quo actions $\\hat{\\boldsymbol{b}}$ are positive, this constraint will be respected for all $C$ less than some $\\hat{C}$",
    "explanation": "$\\hat{\\boldsymbol{b}}$ is consistently introduced and used throughout the paper as the vector of status quo *standalone marginal returns*, not actions. The status quo equilibrium actions are $\\hat{\\boldsymbol{a}}^* = [I-\\beta G]^{-1}\\hat{\\boldsymbol{b}}$. Labelling $\\hat{\\boldsymbol{b}}$ as 'actions' here is a terminological error that contradicts the paper's own definitions.",
    "fix": "Change \"status quo actions $\\hat{\\boldsymbol{b}}$\" to \"status quo standalone marginal returns $\\hat{\\boldsymbol{b}}$\" (or, if positivity of the equilibrium actions is intended, refer to $\\hat{\\boldsymbol{a}}^*$)."
  },
  {
    "category": "typo",
    "severity": "major",
    "title": "Missing exponent $^2$ on $\\underline{\\hat{b}}_\\ell$ in the Lagrangian",
    "snippet": "\\mathcal{L}=w \\sum_{\\ell=1}^{n} \\alpha_{\\ell}\\left(1+x_{\\ell}\\right)^{2} \\underline{\\hat{b}}_{\\ell}+\\mu\\left[C-\\sum_{\\ell=1}^{n} \\hat{b}_{\\ell}^{2} x_{\\ell}^{2}\\right]",
    "explanation": "The maximization problem immediately above (IT-PC transformed) has objective $w\\sum_\\ell \\alpha_\\ell(1+x_\\ell)^2 \\underline{\\hat{b}}_\\ell^{\\mathbf{2}}$. The Lagrangian must reflect the same objective; the missing $^2$ on $\\underline{\\hat{b}}_\\ell$ is inconsistent with both the problem statement and the subsequent first-order conditions.",
    "fix": "Change $\\underline{\\hat{b}}_{\\ell}$ to $\\underline{\\hat{b}}_{\\ell}^{2}$ in the first sum of the Lagrangian."
  },
  {
    "category": "typo",
    "severity": "minor",
    "title": "Misspelling: \"faciliates\" \u2192 \"facilitates\"",
    "snippet": "The last part of the assumption is technical; it holds for generic status quo vectors $\\hat{\\boldsymbol{b}}$ (or generic $\\boldsymbol{G}$ fixing a status quo vector) and faciliates a description of the optimal intervention",
    "explanation": "\"faciliates\" is missing the letter 't' and should be \"facilitates\".",
    "fix": "Replace \"faciliates\" with \"facilitates\"."
  },
  {
    "category": "typo",
    "severity": "minor",
    "title": "Missing sum index: $\\sum_{\\in \\mathcal{N}}$ should be $\\sum_{i \\in \\mathcal{N}}$",
    "snippet": "K(\\mathcal{B})= \\begin{cases}\\phi\\left(\\sum_{\\in \\mathcal{N}} \\sigma_{i i}^{\\mathcal{B}}\\right)",
    "explanation": "The summation subscript is written as $\\sum_{\\in \\mathcal{N}}$, omitting the index variable $i$. Every other summation over $\\mathcal{N}$ in the paper (e.g., the cost function in the main model) uses $\\sum_{i \\in \\mathcal{N}}$.",
    "fix": "Change $\\sum_{\\in \\mathcal{N}}$ to $\\sum_{i \\in \\mathcal{N}}$."
  },
  {
    "category": "typo",
    "severity": "minor",
    "title": "Word run-together: \"largesteigenvalue\" missing hyphen/space",
    "snippet": "Under strategic complements, this is the first (largesteigenvalue) eigenvector of the network",
    "explanation": "\"largesteigenvalue\" is a typesetting artefact where the hyphen and/or space between \"largest\" and \"eigenvalue\" was dropped.",
    "fix": "Change \"(largesteigenvalue)\" to \"(largest-eigenvalue)\"."
  },
  {
    "category": "grammar",
    "severity": "minor",
    "title": "Singular possessive \"individual's\" should be plural \"individuals'\"",
    "snippet": "Shocks to individual's standalone marginal returns create variability in the players' equilibrium actions.",
    "explanation": "The sentence refers to shocks affecting multiple individuals' returns, so the plural possessive \"individuals'\" is required.",
    "fix": "Change \"individual's standalone marginal returns\" to \"individuals' standalone marginal returns\"."
  },
  {
    "category": "clarity",
    "severity": "minor",
    "title": "Redundant \"Figure\" in cross-reference to multiple subfigures",
    "snippet": "see Figures 3(B) and Figure 3(D)",
    "explanation": "\"Figures\" (plural) is opened at the start, but the second subfigure is introduced again with a redundant singular \"Figure\". Standard academic style would read \"Figures 3(B) and 3(D)\".",
    "fix": "Change \"see Figures 3(B) and Figure 3(D)\" to \"see Figures 3(B) and 3(D)\"."
  },
  {
    "category": "terminology_consistency",
    "severity": "minor",
    "title": "Inconsistent spelling of journal name: \"Behaviour\" vs \"Behavior\"",
    "snippet": "Demange, G. (2017): \"Optimal Targeting Strategies in a Network Under Complementarities,\" Games and Economic Behaviour, 105, 84-103.",
    "explanation": "All other references to the same journal (Bloch and Querou 2013, Leduc et al. 2017) use the American spelling \"Games and Economic Behavior\". The Demange (2017) entry uses the British variant \"Behaviour\". The reference list should use a single consistent spelling throughout.",
    "fix": "Change \"Games and Economic Behaviour\" to \"Games and Economic Behavior\" in the Demange (2017) reference."
  },
  {
    "category": "typo",
    "severity": "minor",
    "title": "Missing comma in reference author list: \"B. Golub S. Goyal\"",
    "snippet": "Galeotti, A., B. Golub S. Goyal (2020): \"Supplement to 'Targeting Interventions in Networks,'\"",
    "explanation": "A comma is missing between \"Golub\" and \"S. Goyal\" in the author list.",
    "fix": "Change \"B. Golub S. Goyal\" to \"B. Golub, and S. Goyal\"."
  },
  {
    "category": "typo",
    "severity": "minor",
    "title": "Misspelling: \"Eonomics\" \u2192 \"Economics\" in reference affiliation",
    "snippet": "Golub, B., and S. Morris (2020): \"Expectations, Networks and Conventions,\" Report, Department of Eonomics, Harvard University",
    "explanation": "\"Eonomics\" is missing the letter 'c' and should be \"Economics\".",
    "fix": "Replace \"Eonomics\" with \"Economics\"."
  }
]
```

### notation-tracker from claude:opus

```json
[
  {
    "category": "notation_drift",
    "severity": "critical",
    "title": "Cosine similarity definition missing \u2016z\u2016 in denominator",
    "snippet": "DEFINITION 1: The cosine similarity of two nonzero vectors $\\boldsymbol{y}$ and $\\boldsymbol{z}$ is $\\rho(\\boldsymbol{y}, \\boldsymbol{z})=\\frac{\\boldsymbol{y} \\cdot \\boldsymbol{z}}{\\|\\boldsymbol{y}\\|}$.",
    "explanation": "The definition gives \u03c1(y,z)= (y\u00b7z)/\u2016y\u2016, but the standard cosine similarity\u2014and the formula used in every proof (e.g., line 490: y*\u00b7u^\u2113 / (\u2016y*\u2016 \u2016u^\u2113\u2016), and line 572)\u2014divides by \u2016y\u2016\u2016z\u2016. The denominator is missing \u2016z\u2016. Although eigenvectors satisfy \u2016u^\u2113\u2016=1 so the omission is invisible in most applications, the definition as stated is mathematically wrong for general vectors.",
    "fix": "Change the definition to $\\rho(\\boldsymbol{y}, \\boldsymbol{z})=\\frac{\\boldsymbol{y} \\cdot \\boldsymbol{z}}{\\|\\boldsymbol{y}\\|\\|\\boldsymbol{z}\\|}$."
  },
  {
    "category": "notation_drift",
    "severity": "critical",
    "title": "Self-referential change of variables in Example 2: b_i defined in terms of b_i",
    "snippet": "Performing the change of variables $b_{i}=[\\tau-b_{i}] / 2$ and $\\beta=-\\tilde{\\beta} / 2$",
    "explanation": "Line 128 writes b_i = [\u03c4 \u2212 b_i]/2, defining b_i in terms of itself. From context and from footnote 15 (line 735), which correctly writes b_i = [\u03c4 \u2212 \\tilde{b}_i]/2, the tilde on b_i on the right-hand side was dropped. This makes the change of variables circular and undefined.",
    "fix": "Replace $b_{i}=[\\tau-b_{i}] / 2$ with $b_{i}=[\\tau-\\tilde{b}_{i}] / 2$."
  },
  {
    "category": "sign_inconsistency",
    "severity": "critical",
    "title": "Assumption 3 missing squared norm: C < \u2016b\u0302\u2016 should be C < \u2016b\u0302\u2016\u00b2",
    "snippet": "Assumption 3: Either $w<0$ and $C<\\|\\hat{\\boldsymbol{b}}\\|$, or $w>0$.",
    "explanation": "Two lines earlier (line 198), the text states the first-best is achievable when C \u2265 \u2016b\u0302\u2016\u00b2. Assumption 3 is meant to rule out this case, so the condition should be C < \u2016b\u0302\u2016\u00b2. As written, C < \u2016b\u0302\u2016 is dimensionally inconsistent with the quadratic cost function K = \u03a3(b_i \u2212 b\u0302_i)\u00b2, which has units of b\u00b2 not b. Footnote 34 (line 770) also confirms the correct threshold is \u03a3 b\u0302_\u2113\u00b2 (= \u2016b\u0302\u2016\u00b2).",
    "fix": "Change to $C<\\|\\hat{\\boldsymbol{b}}\\|^{2}$."
  },
  {
    "category": "notation_drift",
    "severity": "major",
    "title": "Scalar \u03b2 incorrectly bolded as \ud835\udec3 in diagonal system",
    "snippet": "$[\\boldsymbol{I}-\\boldsymbol{\\beta} \\boldsymbol{\\Lambda}]^{-1}$ is $\\frac{1}{1-\\beta \\lambda_{\\ell}}$",
    "explanation": "At lines 175 and 436, the scalar parameter \u03b2 is typeset in bold (\\boldsymbol{\u03b2}), suggesting it is a vector or matrix. In every other occurrence (equations (2), (3), (4), Theorem 1, all proofs), \u03b2 is an unbolded scalar. The bold is applied only when \u03b2 appears between two bold matrices I and \u039b, likely a copy-paste artifact.",
    "fix": "Replace $\\boldsymbol{\\beta}$ with $\\beta$ at both occurrences."
  },
  {
    "category": "notation_drift",
    "severity": "major",
    "title": "Missing boldface on vectors in equation (2) and line 166",
    "snippet": "$[I-\\beta G] a^{*}=b$  (line 57)\n$[I-\\beta \\boldsymbol{U} \\boldsymbol{\\Lambda} \\boldsymbol{U}^{\\top}] a^{*}=b$  (line 166)",
    "explanation": "Equation (2) writes I, a*, and b without boldface, but equation (3) immediately after writes [\ud835\udc08\u2212\u03b2\ud835\udc06]\u207b\u00b9\ud835\udc1b with full boldface. Similarly, line 166 mixes bolded U, \u039b with unbolded I, a*, b. The paper's convention (established in \u00a72) is that matrices and vectors are bold.",
    "fix": "Write $[\\boldsymbol{I}-\\beta \\boldsymbol{G}] \\boldsymbol{a}^{*}=\\boldsymbol{b}$ in equation (2), and similarly in line 166."
  },
  {
    "category": "notation_drift",
    "severity": "major",
    "title": "Missing boldface on y* in Theorem 1 and similarity ratio definition",
    "snippet": "$\\rho(y^{*}, \\boldsymbol{u}^{\\ell}(\\boldsymbol{G}))$ (lines 214, 249)",
    "explanation": "The vector y* is defined with bold on line 203 as \ud835\udc32* = \ud835\udc1b* \u2212 \ud835\udc1b\u0302 and appears bolded in all other places (lines 239, 295, 504). However, in the statement of Theorem 1 (line 214) and the definition of the similarity ratio r*_\u2113 (line 249), y* appears without bold, breaking the convention for vectors.",
    "fix": "Replace $y^{*}$ with $\\boldsymbol{y}^{*}$ in equations (5) and (7)."
  },
  {
    "category": "notation_drift",
    "severity": "major",
    "title": "Underline notation inconsistently dropped on b\u0302_\u2113 in principal-component basis",
    "snippet": "Thm 1 eq (6): $\\hat{b}_{\\ell}^{2}$ vs. sketch eq (8): $\\hat{\\underline{b}}_{\\ell}^{2}$",
    "explanation": "The paper defines z\u0332 = U\u22a4z (line 163) to denote projections in the principal-component basis. In the reformulated problem (line 227), b\u0332\u0302_\u2113 is correctly underlined. But in Theorem 1's own equation (6) (line 220), and throughout the proof's Lagrangian (line 465), FOC (line 471), budget condition (line 483), and lines 491, 532\u2013557, the underline is dropped and the symbol is written as b\u0302_\u2113. Since b\u0302_i (subscript i) denotes the i-th individual's status quo return in the original basis, the missing underline creates genuine ambiguity about which basis is intended.",
    "fix": "Consistently write $\\underline{\\hat{b}}_{\\ell}$ (with underline) whenever the subscript is \u2113 and the quantity is a principal-component projection."
  },
  {
    "category": "notation_drift",
    "severity": "major",
    "title": "Lagrangian missing square on b\u0332\u0302_\u2113 in objective term",
    "snippet": "$\\mathcal{L}=w \\sum_{\\ell=1}^{n} \\alpha_{\\ell}(1+x_{\\ell})^{2} \\underline{\\hat{b}}_{\\ell}+\\mu[C-\\sum_{\\ell=1}^{n} \\hat{b}_{\\ell}^{2} x_{\\ell}^{2}]$",
    "explanation": "In the Lagrangian (line 465), the first sum has \\underline{\\hat{b}}_{\u2113} without a square, while the objective being optimized (lines 451\u2013452) has \\underline{\\hat{b}}_{\u2113}\u00b2. The square is required; without it the Lagrangian does not match the objective and the FOC derivation does not follow.",
    "fix": "Change $\\underline{\\hat{b}}_{\\ell}$ to $\\underline{\\hat{b}}_{\\ell}^{2}$ in the first sum of the Lagrangian."
  },
  {
    "category": "sign_inconsistency",
    "severity": "major",
    "title": "Denominator ordering reversed: \u03b1_{n-1}/(\u03b1_{n-1}\u2212\u03b1_n) vs. Proposition 2's \u03b1_{n-1}/(\u03b1_n\u2212\u03b1_{n-1})",
    "snippet": "the term $\\alpha_{n-1} /(\\alpha_{n-1}-\\alpha_{n})$ of the inequality is large when $\\lambda_{n-1}-\\lambda_{n}$...is small.",
    "explanation": "Line 301 discusses the bound from Proposition 2 part 2 (line 296), which contains (\u03b1_{n-1}/(\u03b1_n \u2212 \u03b1_{n-1}))\u00b2. For \u03b2<0, \u03b1_n > \u03b1_{n-1}, so \u03b1_n \u2212 \u03b1_{n-1} > 0 and the Proposition's expression is positive. However, the text writes \u03b1_{n-1}/(\u03b1_{n-1} \u2212 \u03b1_n), which is negative. Although the bound squares the term (hiding the sign), the text discusses it unsquared as being 'large', which is incoherent for a negative quantity.",
    "fix": "Change $\\alpha_{n-1}/(\\alpha_{n-1}-\\alpha_{n})$ to $\\alpha_{n-1}/(\\alpha_{n}-\\alpha_{n-1})$ to match Proposition 2."
  },
  {
    "category": "sign_inconsistency",
    "severity": "major",
    "title": "Eigenvectors u^n, u^{n-1} called 'maximizers' of minimization problems",
    "snippet": "Moreover, the eigenvector $\\boldsymbol{u}^{n}$ is a maximizer of the first problem, while $\\boldsymbol{u}^{n-1}$ is a maximizer of the second",
    "explanation": "Line 324 refers to the problems on line 321\u2013322, which define \u03bb_n and \u03bb_{n-1} via min, not max. The eigenvectors u^n and u^{n-1} are therefore minimizers of the corresponding Rayleigh quotient problems. Compare with line 316, which correctly says u^1 is a 'maximizer' of the \u03bb_1 = max problem.",
    "fix": "Replace 'maximizer' with 'minimizer' in both instances on line 324."
  },
  {
    "category": "subscript_inconsistency",
    "severity": "major",
    "title": "Eigenvector entry subscript/superscript reversed: u^i_\u2113 vs. u^\u2113_i",
    "snippet": "$b_{i}^{*}-\\hat{b}_{i}=w \\sum_{\\ell=1}^{n} u_{\\ell}^{i} \\frac{\\alpha_{\\ell}}{\\mu-w \\alpha_{\\ell}} \\hat{b}_{\\ell}$",
    "explanation": "The paper's convention (established at line 186: a*_i = \u03a3_\u2113 (1/(1\u2212\u03b2\u03bb_\u2113)) u^\u2113_i b\u0332_\u2113) is that u^\u2113_i means the i-th entry of the \u2113-th eigenvector (superscript = eigenvector index, subscript = node index). Line 584 writes u^i_\u2113, reversing the indices. While U is orthogonal so numerically U_{i\u2113}=U_{\u2113i} is false in general, this notation swap is confusing.",
    "fix": "Replace $u_{\\ell}^{i}$ with $u_{i}^{\\ell}$ on line 584."
  },
  {
    "category": "undefined_symbol",
    "severity": "minor",
    "title": "Spurious asterisk on \u03b1\u2082 in proof of Proposition 2",
    "snippet": "$1+\\frac{2 \\alpha_{1}-\\alpha_{2}^{*}}{\\alpha_{1}} \\frac{\\|\\hat{\\boldsymbol{b}}\\|^{2}}{C}\\left(\\frac{\\alpha_{2}}{\\alpha_{1}-\\alpha_{2}}\\right)^{2}$",
    "explanation": "Line 543 writes \u03b1\u2082* (with asterisk), but \u03b1*_\u2113 is never defined; the asterisk likely crept in from the adjacent x*_\u2113 terms. The derivation (line 557) yields the factor (2\u03b1\u2081 \u2212 \u03b1\u2082), with no asterisk on \u03b1\u2082. The next line (544) correctly bounds this by 2, confirming the intended quantity is just \u03b1\u2082.",
    "fix": "Replace $\\alpha_{2}^{*}$ with $\\alpha_{2}$."
  },
  {
    "category": "notation_drift",
    "severity": "minor",
    "title": "Double-hat \\hat{\\hat{b}}_\u2113\u00b2 in definition of D (proof of Prop 2)",
    "snippet": "letting $D=\\underline{\\hat{b}}_{1}^{2} \\alpha_{1} \\tilde{x}_{1}(\\tilde{x}_{1}+2)+\\sum_{\\ell=1}^{n} \\alpha_{\\ell} \\hat{\\hat{b}}_{\\ell}^{2}$",
    "explanation": "Line 535 has \\hat{\\hat{b}}_\u2113\u00b2 (double hat). No symbol with two hats is defined anywhere. From context (matching W^s on line 526), this should be \\underline{\\hat{b}}_\u2113\u00b2 (underline + single hat).",
    "fix": "Replace $\\hat{\\hat{b}}_{\\ell}^{2}$ with $\\underline{\\hat{b}}_{\\ell}^{2}$."
  },
  {
    "category": "notation_drift",
    "severity": "minor",
    "title": "Transpose/asterisk misplaced in expected welfare formula",
    "snippet": "$w \\mathbb{E}[(\\underline{\\boldsymbol{a}}^{\\top})^{*}(\\underline{\\boldsymbol{a}}^{*})]$",
    "explanation": "Line 353 writes (a\u0332\u22a4)* instead of (a\u0332*)\u22a4. The asterisk denotes the equilibrium and should be on a\u0332 before the transpose is applied, i.e. (a\u0332*)\u22a4(a\u0332*). As written, the asterisk appears to be applied to the already-transposed vector, which is notationally anomalous.",
    "fix": "Replace $(\\underline{\\boldsymbol{a}}^{\\top})^{*}(\\underline{\\boldsymbol{a}}^{*})$ with $(\\underline{\\boldsymbol{a}}^{*})^{\\top}(\\underline{\\boldsymbol{a}}^{*})$."
  },
  {
    "category": "subscript_inconsistency",
    "severity": "minor",
    "title": "Prime on \u03b1 rendered as superscript rather than subscript: \u03b1'_\u2113 vs \u03b1_{\u2113'}",
    "snippet": "$\\frac{r_{\\ell}^{*}}{r_{\\ell^{\\prime}}^{*}}=\\frac{\\alpha_{\\ell}}{\\alpha_{\\ell^{\\prime}}} \\frac{\\mu-w \\alpha_{\\ell}^{\\prime}}{\\mu-w \\alpha_{\\ell}}$",
    "explanation": "Line 498 writes \u03b1'_\u2113 (prime as superscript on \u03b1 with subscript \u2113) in the numerator of the second fraction, but the intended quantity is \u03b1_{\u2113'} (subscript \u2113'). The left-hand side correctly uses \u2113' as a subscript on r*, and \u03b1_{\u2113'} appears correctly in the first fraction's denominator. The misplaced prime on \u03b1 could be read as a derivative.",
    "fix": "Replace $\\alpha_{\\ell}^{\\prime}$ with $\\alpha_{\\ell^{\\prime}}$."
  },
  {
    "category": "undefined_symbol",
    "severity": "minor",
    "title": "Missing summation index i in cost function (10)",
    "snippet": "$K(\\mathcal{B})= \\phi(\\sum_{\\in \\mathcal{N}} \\sigma_{ii}^{\\mathcal{B}})$",
    "explanation": "Line 384 writes \u03a3_{\u2208\ud835\udca9} with no index variable before the \u2208 symbol. The surrounding text discusses 'the sum of the variances of the b_i', confirming the missing index is i.",
    "fix": "Replace $\\sum_{\\in \\mathcal{N}}$ with $\\sum_{i \\in \\mathcal{N}}$."
  },
  {
    "category": "notation_drift",
    "severity": "minor",
    "title": "New symbol \u0394b* introduced without definition in proof of Proposition 2",
    "snippet": "$\\rho(\\Delta \\boldsymbol{b}^{*}, \\sqrt{C} \\boldsymbol{u}^{1})$",
    "explanation": "Lines 572 and 596 use \u0394b* to denote b* \u2212 b\u0302, but this symbol is never formally defined. The rest of the paper (and the definition on line 203) uses y* = b* \u2212 b\u0302 for this quantity. The proof itself expands \u0394b* as (b* \u2212 b\u0302), confirming it is just y*, making the new notation unnecessary and potentially confusing.",
    "fix": "Replace $\\Delta \\boldsymbol{b}^{*}$ with $\\boldsymbol{y}^{*}$ to match the notation established in Section 4."
  }
]
```
