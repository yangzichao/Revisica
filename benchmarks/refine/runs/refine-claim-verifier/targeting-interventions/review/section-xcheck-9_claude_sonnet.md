```json
{
  "findings": [
    {
      "category": "logic_gap",
      "severity": "major",
      "title": "Residual matrix definition omits eigenvalue scaling, breaking the iterative PCA procedure",
      "snippet": "G^{(2)} = G - u^1(u^1)^\\top",
      "explanation": "Section 3 defines the iterative residual as G^(2) = G − u^1(u^1)^⊤, but Fact 1 (which derives directly from the Section 2 spectral framework) establishes G = UΛU^⊤, so the rank-1 component corresponding to the first principal direction is λ₁·u^1(u^1)^⊤, not u^1(u^1)^⊤. The text itself flags this inconsistency: it correctly states that the minimizer of Σ(g_ij − u_i u_j)² is 'a scaling of the eigenvector u^1' (i.e., the minimising vector is c·u^1, yielding the rank-1 matrix λ₁·u^1(u^1)^⊤ by Eckart–Young), yet the residual formula drops the eigenvalue scalar. As written, G − u^1(u^1)^⊤ retains u^1 as an eigenvector with eigenvalue λ₁ − 1, so the next step of the procedure does not recover u^2 as the leading eigenvector unless λ₁ = 1 coincidentally. The correct residual is G − λ₁·u^1(u^1)^⊤ = Σ_{ℓ≥2} λ_ℓ u^ℓ(u^ℓ)^⊤, which cleanly yields u^2 on the next iteration.",
      "fix": "Change the residual definition to G^{(2)} = \\boldsymbol{G} - \\lambda_1 \\boldsymbol{u}^1(\\boldsymbol{u}^1)^{\\top}, consistent with the spectral decomposition in Fact 1 and the Eckart–Young theorem. Optionally note that the minimising vector is \\sqrt{\\lambda_1}\\,\\boldsymbol{u}^1, so the best rank-1 matrix is \\lambda_1 \\boldsymbol{u}^1(\\boldsymbol{u}^1)^{\\top}."
    },
    {
      "category": "notation_mismatch",
      "severity": "minor",
      "title": "Fact 1 uses weak eigenvalue ordering (≥) despite Assumption 2 guaranteeing strict distinctness",
      "snippet": "\\lambda_{1} \\geq \\lambda_{2} \\geq \\cdots \\geq \\lambda_{n}",
      "explanation": "Section 2's Assumption 2 explicitly requires 'all eigenvalues of G are distinct,' which means the ordering should be strict throughout: λ₁ > λ₂ > ··· > λₙ. Fact 1 in Section 3 uses weak inequalities (≥), which technically allows repeated eigenvalues that Assumption 2 has already ruled out. While mathematically the weak form is not false (strict implies weak), the inconsistency can mislead readers into thinking Fact 1 is stated in greater generality than the rest of the paper's framework permits, and it obscures that the uniqueness claim ('the decomposition is uniquely determined') follows directly from Assumption 2 rather than from 'generic G'.",
      "fix": "Replace \\lambda_{1} \\geq \\lambda_{2} \\geq \\cdots \\geq \\lambda_{n} with \\lambda_{1} > \\lambda_{2} > \\cdots > \\lambda_{n} in Fact 1 (since Assumption 2 is already in force), and replace 'For generic G, the decomposition is uniquely determined' with 'Under Assumption 2, the decomposition is uniquely determined'."
    },
    {
      "category": "flow_break",
      "severity": "minor",
      "title": "Section 3 opening sentence promises simplification of the planner's objective, but does not deliver it in the section",
      "snippet": "This section introduces a basis for the space of standalone marginal returns and actions in which, under our assumptions on \\boldsymbol{G}, strategic effects and the planner's objective both take a simple form.",
      "explanation": "The opening sentence claims Section 3 shows that both 'strategic effects' and 'the planner's objective' take a simple form in the principal-component basis. Section 3 as presented establishes the spectral decomposition and its PCA interpretation (strategic effects), but the simplification of the planner's welfare objective — the core of the IT problem formulated at the end of Section 2 — is not demonstrated until Section 3.1 and Section 4. A reader arriving from Section 2's IT problem formulation will expect both promises to be fulfilled within this section, creating a perceived gap. No forward reference is provided to bridge this.",
      "fix": "Either narrow the opening sentence to what Section 3 actually delivers: '…in which strategic effects take a simple form, laying the groundwork for Section 3.1, which shows how the planner's objective simplifies in this basis.' Alternatively, add an explicit forward pointer such as '(see Section 3.1)' after 'the planner's objective both take a simple form.'"
    }
  ]
}
```

**Summary of findings across the Section 2 → Section 3 transition:**

| # | Category | Severity | Issue |
|---|----------|----------|-------|
| 1 | `logic_gap` | **major** | `G^{(2)} = G - u^1(u^1)^\top` drops the `λ₁` scalar required by the spectral decomposition; the residual should be `G − λ₁u^1(u^1)^⊤` so that `u^2` correctly emerges as the next leading direction |
| 2 | `notation_mismatch` | minor | Fact 1 uses `λ₁ ≥ λ₂ ≥ ··· ≥ λₙ` (weak), but Assumption 2 (Section 2) already guarantees all eigenvalues are **distinct**, so strict inequalities should be used |
| 3 | `flow_break` | minor | Section 3's opening sentence promises both strategic-effects *and* planner-objective simplification, but only the former is shown in the section body; the latter appears in Section 3.1/4 without a forward reference |
