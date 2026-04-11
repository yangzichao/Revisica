The claim has been verified both symbolically and numerically. Here's the reasoning:

**Equation (6):** $\sum_{\ell=1}^{n}\left(\frac{w \alpha_{\ell}}{\mu-w \alpha_{\ell}}\right)^{2} \hat{b}_{\ell}^{2}=C$

Defining $F(\mu, C) = \sum_\ell \left(\frac{w\alpha_\ell}{\mu - w\alpha_\ell}\right)^2 \hat{b}_\ell^2 - C = 0$, by the implicit function theorem:

- $\partial F/\partial C = -1$
- $\partial F/\partial \mu = \sum_\ell \frac{-2(w\alpha_\ell)^2 \hat{b}_\ell^2}{(\mu - w\alpha_\ell)^3} < 0$ (since $\mu > w\alpha_\ell > 0$)
- $d\mu/dC = -\frac{\partial F/\partial C}{\partial F/\partial \mu} = \frac{-1}{\text{negative}} < 0$

So μ is strictly decreasing in C. The secondary claims (that $\frac{w\alpha_\ell}{\mu - w\alpha_\ell}$ increases in C, and that ratio $r_\ell^*/r_{\ell'}^*$ increases in C when $\alpha_\ell > \alpha_{\ell'}$) were also confirmed numerically.

```json
{"findings": []}
```
