```json
{
  "findings": [
    {
      "category": "notation_mismatch",
      "severity": "major",
      "title": "'Private returns to investment' (Abstract) vs. 'standalone marginal returns' (Introduction)",
      "snippet": "Abstract: \"…interventions that change individual's private returns to investment\"\nIntroduction: \"…alter their standalone marginal returns from status quo levels\"",
      "explanation": "The Abstract introduces the intervention target as 'private returns to investment,' but this phrase never reappears. The Introduction uses 'standalone marginal returns' exclusively and repeatedly — it is the term tied to the formal model and to all subsequent results (Theorem 1, Propositions 1–4). Because no bridging sentence equates the two, a reader moving from the Abstract to the Introduction cannot immediately confirm these are the same primitive. The mismatch is especially confusing because 'private returns to investment' carries a different connotation (it could suggest ownership or asset-return framing) from 'standalone marginal returns' (a partial-equilibrium incentive concept).",
      "fix": "Replace 'private returns to investment' in the Abstract with 'standalone marginal returns' to align with the terminology used throughout the paper."
    },
    {
      "category": "claim_inconsistency",
      "severity": "major",
      "title": "Abstract's 'simple' interventions omit the invariance-to-primitives condition given in the Introduction",
      "snippet": "Abstract: \"For large budgets, optimal interventions are simple—they essentially involve only a single principal component.\"\nIntroduction: \"simple optimal interventions, that is, ones where the relative intervention on the incentives of each node is determined by a single network statistic of that node, and invariant to other primitives (such as status quo incentives).\"",
      "explanation": "The Abstract defines simplicity purely in spectral terms (one principal component), while the Introduction gives a two-part definition: (1) driven by a single network statistic, and (2) invariant to status quo incentives. The invariance condition is the practically important part — it is what allows a planner lacking individual-level data to still implement the optimal policy. Omitting it in the Abstract misrepresents the result as a spectral tidiness claim rather than a robustness/implementability guarantee. Additionally, the Abstract hedges with 'essentially,' whereas Propositions 1 and 2 in the Introduction establish exact proportionality, not approximation.",
      "fix": "Revise the Abstract's sentence to include the invariance condition and drop the hedging qualifier, e.g., '…optimal interventions are simple: each depends only on a single network statistic of the targeted individual and is invariant to status quo incentives.'"
    },
    {
      "category": "logic_gap",
      "severity": "minor",
      "title": "Abstract merges 'spillovers' and 'externalities' into one undifferentiated channel that the Introduction explicitly separates",
      "snippet": "Abstract: \"a network mediates strategic spillovers and externalities among the players\"\nIntroduction: \"This happens through two channels: spillover effects on others' incentives, as well as non-strategic externalities.\"",
      "explanation": "The Abstract's opening treats spillovers and externalities as a joint phenomenon. The Introduction immediately splits them into categorically distinct channels: incentive spillovers (strategic, affecting marginal returns and therefore equilibrium actions) and non-strategic externalities (affecting welfare but not incentives). The distinction is load-bearing because the planner's tool — changing standalone marginal returns — interacts with incentive spillovers but not directly with non-strategic externalities. A reader finishing the Abstract has no preparation for this conceptual split, creating a mild logical discontinuity at the section boundary.",
      "fix": "Revise the Abstract to flag the two-channel structure, e.g., '…a network mediates strategic spillovers — which affect agents' marginal incentives — and non-strategic externalities among players.'"
    },
    {
      "category": "notation_mismatch",
      "severity": "minor",
      "title": "'Matrix of interactions' and 'network of strategic interactions' used interchangeably within the Introduction; Abstract uses only 'the network'",
      "snippet": "Introduction (principal-components paragraph): \"…the principal components, or eigenvectors, of the matrix of interactions\"\nIntroduction (Corollary 1 paragraph): \"…eigenvector centralities in the network of strategic interactions\"\nAbstract: \"…which are determined by the network\"",
      "explanation": "Within the Introduction, two labels — 'matrix of interactions' and 'network of strategic interactions' — refer to the same mathematical object (whose eigenvectors are the principal components of the analysis) but are never equated. The Abstract uses the unqualified 'the network,' which could also encompass the externality structure. Since the model distinguishes strategic interaction links from externality links, it is ambiguous across all three uses whether 'the network,' 'the matrix of interactions,' and 'the network of strategic interactions' denote the same object. This creates a potential source of confusion that originates in the Abstract's imprecise reference.",
      "fix": "Pick a single canonical label (e.g., 'network of strategic interactions') at first use in the Introduction and apply it consistently. Update the Abstract to use the same qualified term rather than the bare 'the network.'"
    }
  ]
}
```
