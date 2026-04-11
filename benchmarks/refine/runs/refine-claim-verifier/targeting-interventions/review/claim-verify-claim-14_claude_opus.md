The claim is verified both symbolically and numerically. The logic is straightforward:

1. In the Investment Game, utility is $U_i(\mathbf{a}, \mathbf{G}) = a_i(b_i + \beta \sum_j g_{ij} a_j) - \frac{1}{2}a_i^2$
2. At equilibrium, the best-response condition gives $a_i^* = b_i + \beta \sum_j g_{ij} a_j^*$
3. Substituting: $U_i(\mathbf{a}^*, \mathbf{G}) = a_i^* \cdot a_i^* - \frac{1}{2}(a_i^*)^2 = \frac{1}{2}(a_i^*)^2$
4. Summing: $W(\mathbf{b}, \mathbf{G}) = \frac{1}{2}(\mathbf{a}^*)^\top \mathbf{a}^*$

This was confirmed with multiple numerical tests (different network sizes, both positive and negative $\beta$), all matching to machine precision.

```json
{"findings": []}
```
