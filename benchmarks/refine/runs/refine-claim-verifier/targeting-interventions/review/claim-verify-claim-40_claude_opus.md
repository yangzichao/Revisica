All verifications pass — both numerical (5×5 random case) and symbolic (3×3 exact case). The claim is mathematically correct. Here is the summary:

**Verified identities:**
1. **Norm invariance**: ‖y‖² = ‖U⊤y‖² — holds because U is orthogonal (U⊤U = I)
2. **Norm invariance for actions**: ‖a‖² = ‖U⊤a‖² — same reason
3. **Equilibrium transformation**: [I − βG]a = b transforms to [I − βΛ]a̲ = b̲ — verified by multiplying both sides by U⊤ and using G = UΛU⊤
4. **Component-wise equilibrium**: a̲_ℓ = b̲_ℓ/(1 − βλ_ℓ) — diagonal system
5. **Objective equivalence**: w·a⊤a = w·Σ α_ℓ b̲_ℓ² where α_ℓ = 1/(1 − βλ_ℓ)² — verified symbolically to be exactly zero difference

```json
{"findings": []}
```
