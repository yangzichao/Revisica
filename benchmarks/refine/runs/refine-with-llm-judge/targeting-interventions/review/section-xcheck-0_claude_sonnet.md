```json
{
  "findings": [
    {
      "category": "unsupported_claim",
      "severity": "major",
      "title": "Large-budget simplicity result stated in abstract but absent from conclusion",
      "snippet": "Abstract: \"For large budgets, optimal interventions are simple-they essentially involve only a single principal component.\"",
      "explanation": "The abstract presents the large-budget result — that optimal interventions collapse to essentially a single principal component — as one of the paper's key takeaways. However, the conclusion (Section 6) summarises the main contributions without mentioning this result at all. The conclusion describes the principal-component decomposition and the complements/substitutes weight result, but never restates or alludes to the budget-asymptotic simplification. A reader who reads only the conclusion would have no indication that this result exists, creating an asymmetry between what the abstract promises and what the conclusion delivers.",
      "fix": "Add a sentence in the concluding remarks that restates the large-budget result, e.g., 'We also showed that, as the budget grows large, the optimal intervention simplifies substantially, concentrating essentially on a single principal component.'"
    },
    {
      "category": "notation_mismatch",
      "severity": "minor",
      "title": "Terminology drift: 'private returns to investment' vs. 'standalone marginal returns of actions'",
      "snippet": "Abstract: \"interventions that change individual's private returns to investment\" vs. Conclusion: \"the intervention itself takes the form of altering the standalone marginal returns of actions\"",
      "explanation": "The abstract describes the intervention as changing 'private returns to investment', while the conclusion uses the more precise technical phrase 'standalone marginal returns of actions'. Although both phrases likely refer to the same object, the divergence in wording may confuse readers who try to map the abstract's informal description onto the formal model. 'Investment' also carries a connotation of a lumpy or dynamic decision that is not present in the static action framework described in the conclusion.",
      "fix": "Align the abstract's phrasing with the paper's established terminology: replace 'individual's private returns to investment' with 'standalone marginal returns of actions' (or 'individuals' standalone marginal returns') to ensure consistency with the conclusion and the formal model."
    }
  ]
}
```
