The claim is verified both symbolically and numerically. The key reasoning is:

1. **Assumption 2** states: the spectral radius of $\beta\boldsymbol{G}$ is less than 1, i.e., $\rho(\beta\boldsymbol{G}) < 1$.
2. By the scalar multiplication property of eigenvalues: eigenvalues of $\beta\boldsymbol{G}$ are $\beta\lambda_i(\boldsymbol{G})$, so $\rho(\beta\boldsymbol{G}) = |\beta| \cdot \rho(\boldsymbol{G})$.
3. Therefore $\rho(\beta\boldsymbol{G}) < 1 \iff |\beta| \cdot \rho(\boldsymbol{G}) < 1 \iff |\beta| < 1/\rho(\boldsymbol{G})$, which is exactly what Footnote 8 claims.

Numerical tests across 5 random symmetric matrices confirm the two conditions are always equivalent.

```json
{"findings": []}
```
