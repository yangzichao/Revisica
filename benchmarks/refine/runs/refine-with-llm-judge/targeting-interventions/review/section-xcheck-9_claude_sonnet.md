Now I have the full source. Let me analyse both sections carefully based on the actual text.

**Key mathematical and notational checks:**

1. **PCA residual (line 152):** The stated unconstrained minimiser of $\sum(g_{ij}-u_iu_j)^2$ over free vector $\boldsymbol{u}$ is $\boldsymbol{v}=\sqrt{\lambda_1}\,\boldsymbol{u}^1$ (solving the first-order conditions shows $\|\boldsymbol{u}\|^2 = \lambda_\ell$ at any stationary point, minimised at $\ell=1$). So the best rank-1 approximation is $\boldsymbol{v}\boldsymbol{v}^\top = \lambda_1\boldsymbol{u}^1(\boldsymbol{u}^1)^\top$. The paper then defines $\boldsymbol{G}^{(2)} = \boldsymbol{G} - \boldsymbol{u}^1(\boldsymbol{u}^1)^\top$ — subtracting the **unit-normalised** outer product, **not** the minimiser's outer product $\lambda_1\boldsymbol{u}^1(\boldsymbol{u}^1)^\top$. This residual has eigenvalues $\{\lambda_1-1, \lambda_2,\ldots,\lambda_n\}$, so "the same type of decomposition" on $\boldsymbol{G}^{(2)}$ does **not** recover $\boldsymbol{u}^2$ in general.

2. **Eigenvalue ordering / "generic" in Fact 1 (lines 141, 144):** Assumption 2 imposes that all eigenvalues are *distinct* (so the ordering should be strict $>$). Fact 1 uses weak $\geq$, and the uniqueness statement says "for generic $\boldsymbol{G}$" — but under Assumption 2 the eigenvalues are already stipulated to be distinct, so uniqueness holds for *all* $\boldsymbol{G}$ satisfying the assumption, not merely generically.

3. **Circular change-of-variables in Example 2 (line 128):** The formula reads $b_i = [\tau - b_i]/2$. The status quo on the **same line** correctly writes $\hat{b}_i = [\tau - \tilde{b}_i]/2$, with a tilde. The left-hand occurrence of $b_i$ (the mapped model parameter) is equated to an expression involving $b_i$ itself, rather than the example's $\tilde{b}_i$, making the substitution circular/undefined.

4. **Cosine similarity definition missing $\|\boldsymbol{z}\|$ (line 191–192):** Definition 1 gives $\rho(\boldsymbol{y},\boldsymbol{z}) = \boldsymbol{y}\cdot\boldsymbol{z}/\|\boldsymbol{y}\|$. The text immediately claims "this is the cosine of the angle between the two vectors," which requires $\|\boldsymbol{y}\|\cdot\|\boldsymbol{z}\|$ in the denominator. As written, the formula is not symmetric, not bounded in $[-1,1]$ for general $\boldsymbol{z}$, and the stated special cases ($\rho=1 \Rightarrow$ positive scaling; $\rho=-1 \Rightarrow$ negative scaling) do not follow from this formula for non-unit $\boldsymbol{z}$.

5. **Flow break: Property A → Section 3 motivation:** Section 2 ends on Property A ($W = w(\boldsymbol{a}^*)^\top\boldsymbol{a}^*$). Section 3 opens by asserting the eigenbasis makes "the planner's objective…take a simple form," without even a forward-pointing sentence explaining *why* (the orthonormality of $\boldsymbol{U}$ turns $(\boldsymbol{a}^*)^\top\boldsymbol{a}^*$ into $\sum_\ell(\underline{a}^*_\ell)^2$, i.e., a sum of squares in decoupled components). The motivation is only made concrete in §3.1.

```json
{
  "findings": [
    {
      "category": "logic_gap",
      "severity": "major",
      "title": "Residual matrix G^(2) subtracts unit eigenvector outer product instead of the minimiser's outer product",
      "snippet": "The minimizer turns out to be a scaling of the eigenvector u^1. Now, if we consider the 'residual' matrix G^(2) = G - u^1(u^1)^T, we can perform the same type of decomposition on G^(2) and obtain the second eigenvector u^2 as the best rank-one approximation.",
      "explanation": "The unconstrained minimiser of sum_{i,j}(g_{ij}-u_iu_j)^2 is v = sqrt(lambda_1)*u^1, so the best rank-one approximation is v*v^T = lambda_1*u^1*(u^1)^T. The correct residual for the sequential PCA argument is therefore G - lambda_1*u^1*(u^1)^T, which has eigenvalues {0, lambda_2, ..., lambda_n} and yields u^2 as the next component by the same procedure. The paper instead defines G^(2) = G - u^1*(u^1)^T (subtracting the *unit-normalised* outer product, not the minimiser). This residual has eigenvalues {lambda_1-1, lambda_2, ..., lambda_n}; applying the same minimisation to it does not recover u^2 in general (e.g., if lambda_1 > 2 and lambda_1-1 > |lambda_2|, the procedure would again return u^1 as the leading component). The claim that 'proceeding further in this way gives a sequence of vectors that constitute an orthonormal basis' is therefore unsupported as stated.",
      "fix": "Define the residual consistently with the stated minimisation: G^(2) = G - lambda_1*u^1*(u^1)^T. The sequential construction then recovers the correct eigenvectors because this residual has eigenvalues {0, lambda_2, ..., lambda_n} with the same orthonormal eigenvectors, and repeating the procedure on it yields u^2 as the leading component. Alternatively, reframe by restricting u to be a *unit* vector and define the best rank-one approximation as the matrix u*(u^*)^T (not u*(u^*)^T = lambda_1*u^1*(u^1)^T), but in that case the minimisation problem must be stated with the constraint ||u||=1 to be consistent."
    },
    {
      "category": "notation_mismatch",
      "severity": "minor",
      "title": "Weak inequality in Fact 1 eigenvalue ordering contradicts Assumption 2's strict distinctness; 'generic' qualifier is redundant and inconsistent",
      "snippet": "Assumption 2: ... all eigenvalues of G are distinct. ... lambda_1 >= lambda_2 >= ... >= lambda_n. For generic G, the decomposition is uniquely determined.",
      "explanation": "Assumption 2 explicitly imposes that all eigenvalues of G are distinct. Under this assumption the eigenvalue ordering is necessarily strict (lambda_1 > lambda_2 > ... > lambda_n), but Fact 1 uses weak inequalities (>=), which formally permits repeated eigenvalues and is inconsistent with the active assumption. Additionally, Fact 1 states uniqueness holds 'for generic G,' but under Assumption 2 — which the paper operates under throughout — uniqueness holds for every G satisfying that assumption, not merely generically. The 'generic' qualifier creates a false impression that uniqueness might fail for some G covered by the analysis.",
      "fix": "Change Fact 1's ordering to strict inequalities: lambda_1 > lambda_2 > ... > lambda_n (adding a parenthetical 'under Assumption 2'). Replace 'For generic G, the decomposition is uniquely determined' with 'Under Assumption 2, the decomposition is uniquely determined' to be consistent with the assumption regime in force."
    },
    {
      "category": "notation_mismatch",
      "severity": "major",
      "title": "Circular change-of-variables in Example 2: tilde missing on b_i in the substitution formula",
      "snippet": "Performing the change of variables b_i = [tau - b_i]/2 and beta = -tilde{beta}/2 (with the status quo equal to hat{b}_i = [tau - tilde{b}_i]/2)",
      "explanation": "The formula defines b_i (the model parameter) as a function of b_i itself, which is circular and undefined. The correctly decorated status quo on the same line uses tilde{b}_i (the example's base level introduced in the public-goods utility), confirming the right-hand side of the change of variables should also read tilde{b}_i. As written, the substitution equates b_i = (tau - b_i)/2, implying 3b_i = tau, a nonsensical constraint rather than a parametric mapping. Because this change of variables is the sole link connecting Example 2 to the general model — whose equilibrium, welfare, and IT-problem formulas are then used throughout Section 3 — the error undermines the stated equivalence between the local public-goods game and the canonical model.",
      "fix": "Add the tilde: b_i = [tau - tilde{b}_i]/2. The full corrected sentence reads: 'Performing the change of variables b_i = [tau - tilde{b}_i]/2 and beta = -tilde{beta}/2 (with the status quo equal to hat{b}_i = [tau - tilde{b}_i]/2) yields a best-response structure exactly as in condition (2).'"
    },
    {
      "category": "notation_mismatch",
      "severity": "major",
      "title": "Cosine similarity definition missing ||z|| in denominator; stated equivalences do not follow",
      "snippet": "DEFINITION 1: The cosine similarity of two nonzero vectors y and z is rho(y,z) = y·z / ||y||. This is the cosine of the angle between the two vectors in a plane determined by y and z. When rho(y,z) = 1, the vector z is a positive scaling of y. When rho(y,z) = -1, the vector z is a negative scaling of y.",
      "explanation": "The standard cosine of the angle between y and z is y·z/(||y||·||z||). As defined, rho(y,z) = y·z/||y|| omits ||z|| in the denominator, making it (1) not symmetric (rho(y,z) != rho(z,y) in general), (2) unbounded (not in [-1,1] for arbitrary z), and (3) inconsistent with the claimed special cases: if z = alpha*y with alpha > 0 then rho(y,z) = alpha*||y||, which equals 1 only when alpha = 1/||y||, not for all positive scalings. The claim 'this is the cosine of the angle between the two vectors' is false under this formula for non-unit z. The definition is self-consistent only when z is a unit vector (as the eigenvectors u^ell are), which is the primary use case in the paper but is not stated as a restriction.",
      "fix": "Either (a) add ||z|| to the denominator: rho(y,z) = y·z/(||y||·||z||), giving the standard cosine similarity in [-1,1] with the correct special cases; or (b) explicitly restrict the definition to the case where z is a unit vector and note that in the paper z will always be taken as a principal component u^ell satisfying ||u^ell||=1."
    },
    {
      "category": "flow_break",
      "severity": "minor",
      "title": "Section 3 opening asserts the eigenbasis simplifies the planner's objective without connecting to Property A",
      "snippet": "This section introduces a basis for the space of standalone marginal returns and actions in which, under our assumptions on G, strategic effects and the planner's objective both take a simple form.",
      "explanation": "Section 2 closes with Property A (W = w*(a*)^T*a*) as the key structural feature of the welfare function used in the analysis. Section 3 immediately asserts that the eigenbasis makes 'the planner's objective take a simple form,' but provides no forward pointer or intuitive sentence explaining the connection: orthonormality of U means (a*)^T*a* = (U^T*a*)^T*(U^T*a*) = sum_ell (a*_ell)^2, so Property A becomes a sum of decoupled squared components. Without this bridge, the motivation for introducing the eigenbasis of G specifically is left implicit, and a reader must wait until §3.1 (equation after line 172) to understand why this basis was chosen for the planner's problem.",
      "fix": "Add one sentence linking Property A to the eigenbasis motivation, e.g.: 'In particular, because Property A writes welfare as w*(a*)^T*a* and U is orthonormal, expressing a* in the eigenbasis of G both diagonalises the equilibrium system [I - beta*G]*a* = b and turns the welfare objective into a sum of squared, decoupled components — making the optimal intervention problem tractable.'"
    }
  ]
}
```
