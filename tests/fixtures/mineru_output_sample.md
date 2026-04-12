# Optimal Taxation Under Behavioral Uncertainty

Author: J. Smith, K. Lee

## Abstract

We study the optimal design of commodity taxes when consumers exhibit behavioral biases. Our main result characterizes the optimal tax formula under a general class of behavioral models encompassing both rational and boundedly rational agents.

## 1 Introduction

The classical Ramsey (1927) framework assumes consumers are fully rational. However, a growing body of evidence suggests that consumers systematically misperceive prices, particularly in the presence of sales taxes (Chetty, Looney, and Kroft, 2009). This paper generalizes the Ramsey rule to allow for arbitrary behavioral biases.

We define the *attention parameter* $\theta \in [0,1]$ where $\theta = 1$ corresponds to full rationality and $\theta = 0$ to complete inattention. The consumer's perceived price is:

$$
\tilde{p}_i = p_i + \theta \cdot t_i
$$

where $p_i$ is the producer price and $t_i$ is the per-unit tax on good $i$.

## 2 Model

### 2.1 Consumer Problem

The representative consumer maximizes utility $U(x_1, \ldots, x_n)$ subject to a perceived budget constraint. Let $\lambda$ denote the marginal utility of income. The first-order conditions yield:

$$
\frac{\partial U}{\partial x_i} = \lambda \tilde{p}_i \quad \forall i = 1, \ldots, n
$$

### 2.2 Government Problem

The government chooses taxes $\mathbf{t} = (t_1, \ldots, t_n)$ to maximize social welfare:

$$
\max_{\mathbf{t}} W = \int_0^1 V(\tilde{\mathbf{p}}; \theta) \, d F(\theta)
$$

subject to the revenue constraint:

$$
\sum_{i=1}^{n} t_i \cdot x_i(\tilde{\mathbf{p}}) \geq \bar{R}
$$

## 3 Main Results

**Theorem 1** (Behavioral Ramsey Rule). *Under Assumptions 1--3, the optimal tax on good $i$ satisfies:*

$$
\frac{t_i}{p_i} = \frac{1}{\bar{\theta}} \cdot \frac{\mu}{\mu + 1} \cdot \frac{1}{\epsilon_{ii}}
$$

*where $\bar{\theta} = \mathbb{E}[\theta]$ is the average attention, $\mu$ is the Lagrange multiplier on the revenue constraint, and $\epsilon_{ii}$ is the compensated own-price elasticity.*

*Proof.* Differentiating the Lagrangian with respect to $t_i$ and applying the Slutsky decomposition:

$$
\frac{\partial W}{\partial t_i} = -\lambda \bar{\theta} x_i + \mu \left[ x_i + \sum_j t_j \frac{\partial x_j}{\partial t_i} \right] = 0
$$

Rearranging and using $S_{ij} = \frac{\partial h_j}{\partial \tilde{p}_i}$ for the compensated demand derivatives gives the result. $\blacksquare$

**Proposition 2.** *When $\bar{\theta} < 1$, the optimal tax rate is strictly higher than the standard Ramsey rate. The corrective markup is proportional to $1/\bar{\theta}$.*

## 4 Empirical Application

| Good | Elasticity $\epsilon_{ii}$ | Attention $\bar{\theta}$ | Optimal Rate (%) | Ramsey Rate (%) |
|------|---------------------------|--------------------------|-------------------|-----------------|
| Food | -0.30 | 0.85 | 8.2 | 7.0 |
| Clothing | -0.50 | 0.70 | 11.4 | 8.0 |
| Electronics | -1.20 | 0.45 | 14.8 | 6.7 |
| Alcohol | -0.80 | 0.90 | 5.6 | 5.0 |

## 5 Conclusion

We have shown that behavioral biases systematically alter optimal tax rates. The key insight is that inattention acts as a scaling factor on the standard inverse-elasticity rule.

## References

- Chetty, R., A. Looney, and K. Kroft (2009). "Salience and Taxation: Theory and Evidence." *American Economic Review*, 99(4), 1145--1177.
- Ramsey, F. P. (1927). "A Contribution to the Theory of Taxation." *Economic Journal*, 37(145), 47--61.
