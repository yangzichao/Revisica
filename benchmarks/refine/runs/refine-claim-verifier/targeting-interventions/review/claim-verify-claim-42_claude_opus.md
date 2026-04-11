The claim has been thoroughly verified through three approaches:

1. **Symbolic verification**: The key inequality $(-x+1)^2 - (x+1)^2 = -4x$ confirms that the sign-flipping argument works correctly in both cases.

2. **Numerical optimization**: Six test cases (varying $w > 0$ and $w < 0$, different problem sizes, symmetric and asymmetric $\alpha$ values) all confirm the claim — optimal solutions satisfy $x_\ell^* \geq 0$ when $w > 0$ and $x_\ell^* \in [-1, 0]$ when $w < 0$.

3. **Proof logic verification**: Each step of the paper's argument is mathematically sound — the contradiction-by-improvement arguments are valid for all three sub-cases (flipping sign when $w > 0$, truncating at $-1$ when $w < 0$, and flipping sign when $w < 0$).

```json
{"findings": []}
```
