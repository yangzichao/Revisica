The claim is a standard definitional statement from probability theory. The variance-covariance matrix $\boldsymbol{\Sigma}_{\mathcal{B}}$ has entries $\sigma_{ij}^{\mathcal{B}} = \text{Cov}(b_i, b_j)$. For the diagonal entries where $i = j$:

$$\sigma_{ii}^{\mathcal{B}} = \text{Cov}(b_i, b_i) = \mathbb{E}[(b_i - \mathbb{E}[b_i])^2] = \text{Var}(b_i)$$

Both symbolic and numerical verification confirm this is correct.

```json
{"findings": []}
```
