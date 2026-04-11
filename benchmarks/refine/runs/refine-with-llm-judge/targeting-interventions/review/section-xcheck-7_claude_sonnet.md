```json
{
  "findings": [
    {
      "category": "notation_mismatch",
      "severity": "major",
      "title": "Inconsistent terminology: 'private returns to investment' vs. 'standalone marginal returns'",
      "snippet": "Abstract: 'interventions that change individual's private returns to investment' | Section 1: 'alter their standalone marginal returns from status quo levels'",
      "explanation": "The Abstract labels the object of intervention as 'private returns to investment,' while Section 1 consistently and exclusively uses the technically precise term 'standalone marginal returns' for the same model primitive. These are not standard synonyms: 'standalone' specifically means the return is independent of others' actions, whereas 'private' conventionally contrasts with 'social' and does not carry that meaning. The mismatch risks confusion about whether these refer to the same quantity and is compounded by the substitution of 'investment' for the more general 'action' (which in Section 1 also encompasses 'effort'). Neither phrase appears in the other section.",
      "fix": "Standardize on 'standalone marginal returns' throughout, matching the formal model. In the Abstract, replace 'change individual's private returns to investment' with 'change individuals' standalone marginal returns.'"
    },
    {
      "category": "logic_gap",
      "severity": "minor",
      "title": "Budget constraint invoked in Abstract result but never introduced in Abstract setup",
      "snippet": "Abstract: 'For large budgets, optimal interventions are simple—they essentially involve only a single principal component'",
      "explanation": "The Abstract poses the problem without ever mentioning a resource or budget constraint, yet immediately conditions a key result on budget size ('For large budgets…'). Section 1 gives the budget constraint first-order prominence: 'subject to a budget constraint on the cost of the intervention.' A reader of the Abstract alone cannot understand why budget size is the relevant conditioning variable, making the large-budget result appear unmotivated. The logical antecedent of 'large budgets' is entirely missing from the Abstract's setup.",
      "fix": "Add one clause introducing the constraint in the Abstract's problem setup, e.g., 'A utilitarian planner with a limited budget can intervene to change individuals' standalone marginal returns.' This mirrors Section 1's language and provides the necessary premise for the large-budget result."
    },
    {
      "category": "claim_inconsistency",
      "severity": "minor",
      "title": "Abstract hedges large-budget result with 'essentially,' but Section 1 states it as exact proportionality",
      "snippet": "Abstract: 'they essentially involve only a single principal component' | Section 1 (Propositions 1–2): 'the optimal intervention vector is proportional to the first principal component … proportional to the last one'",
      "explanation": "The qualifier 'essentially' in the Abstract implies approximation or residual multi-component contamination. However, Propositions 1 and 2 in Section 1 establish exact proportionality to a single principal component for large enough budgets — an unhedged, sharp result. The weaker framing in the Abstract understates the strength of the paper's finding and is inconsistent with how the result is presented in the Introduction.",
      "fix": "Remove 'essentially' if the result is indeed exact: 'optimal interventions are simple—they involve only a single principal component.' If 'essentially' is intended to flag that this holds only in the large-budget limit (not for all budgets), rewrite to make that clear, e.g., 'in the limit of large budgets, the optimal intervention converges to a vector proportional to a single principal component.'"
    },
    {
      "category": "unsupported_claim",
      "severity": "minor",
      "title": "Abstract co-bills 'externalities' as central, but all stated results in Section 1 hinge solely on eigenvalue structure of strategic spillovers",
      "snippet": "Abstract: 'a network mediates strategic spillovers and externalities among the players' | Section 1 results description: 'the close relation between the strategic structure of the game … and the appropriate principal components to target'",
      "explanation": "The Abstract's opening presents strategic spillovers and non-strategic externalities as co-equal objects. Section 1 carefully distinguishes these two channels but, when describing the paper's theorems and corollaries (Theorem 1, Corollary 1, Propositions 1–4), frames every result purely in terms of the eigenvalue/principal-component structure of the strategic interaction matrix. Non-strategic externalities are not mentioned in any result statement. The Abstract's framing therefore overstates the structural role of externalities in driving the paper's conclusions.",
      "fix": "Clarify the Abstract to reflect that externalities enter the welfare objective but that the characterization of optimal interventions is governed by the spectral structure of strategic interactions, e.g., 'We study games in which a network mediates strategic spillovers among players, with possible non-strategic externalities affecting social welfare.'"
    }
  ]
}
```

**Summary of the four findings:**

| # | Category | Severity | Issue |
|---|---|---|---|
| 1 | `notation_mismatch` | **Major** | "Private returns to investment" (Abstract) vs. "standalone marginal returns" (Introduction) — different connotations, never reconciled |
| 2 | `logic_gap` | Minor | "For large budgets" appears in Abstract without the budget constraint ever being introduced there |
| 3 | `claim_inconsistency` | Minor | Abstract's hedge "essentially involve only a single principal component" conflicts with the exact proportionality result stated in Propositions 1–2 |
| 4 | `unsupported_claim` | Minor | Abstract foregrounds "externalities" as a co-driver of results, but every theorem and corollary in the Introduction is framed exclusively around eigenvalue structure of strategic spillovers |

The most actionable fix is **Finding 1**: aligning the Abstract's terminology to "standalone marginal returns" would immediately resolve the most prominent inconsistency without requiring any substantive change to the results.
