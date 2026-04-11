# TARGETING INTERVENTIONS IN NETWORKS

Andrea Galeotti<br>Department of Economics, London Business School<br>Benjamin Golub<br>Department of Economics, Harvard University<br>Sanjeev Goyal<br>Faculty of Economics and Christ's College, University of Cambridge

#### Abstract

We study games in which a network mediates strategic spillovers and externalities among the players. How does a planner optimally target interventions that change individual's private returns to investment? We analyze this question by decomposing any intervention into orthogonal principal components, which are determined by the network and are ordered according to their associated eigenvalues. There is a close connection between the nature of spillovers and the representation of various principal components in the optimal intervention. In games of strategic complements (substitutes), interventions place more weight on the top (bottom) principal components, which reflect more global (local) network structure. For large budgets, optimal interventions are simple-they essentially involve only a single principal component.

Keywords: Targeting, interventions, networks, strategic interaction, externalities, peer effects, network games.

## 1. INTRODUCTION

We study games among agents embedded in a network. The action of each agent-for example, a level of investment or effort-directly affects a subset of others, called neighbors of that agent. This happens through two channels: spillover effects on others' incentives, as well as non-strategic externalities. A utilitarian planner with limited resources can intervene to change individuals' incentives for taking the action. Our goal is to understand how the planner can best target such interventions in view of the network and other primitives of the environment.

We now lay out the elements of the model in more detail. Individuals play a simultaneous-move game with continuous actions. An agent's action creates standalone returns for that agent independent of anyone else's action, but it also creates spillovers. The intensity of these spillovers is described by a network, with the strength of a link

[^0]between two individuals reflecting how strongly the action of one affects the marginal returns experienced by the other. The effects may take the form of strategic complements or strategic substitutes. In addition to standalone returns and incentive spillovers, there may be positive or negative externalities imposed by network neighbors on each other. ${ }^{1}$ Before this game is played, the planner can target some individuals and alter their standalone marginal returns from status quo levels. The cost of the intervention is increasing in the magnitude of the change and is separable across individuals. The planner seeks to maximize the utilitarian welfare under equilibrium play of the game, subject to a budget constraint on the cost of the intervention. Our results characterize the optimal intervention policy, showing how it depends on the network, the nature of spillovers, the status quo incentives, and the budget.

An intervention on one individual has direct and indirect effects on the incentives of others. These effects depend on the network and on whether the game features strategic substitutes or complements. For example, suppose the planner increases a given individual's standalone marginal returns to effort, thereby increasing his effort. If actions are strategic complements, this will push up the incentives of the targeted individual's neighbors. That will increase the efforts of the neighbors of these neighbors, and so forth, creating aligned feedback effects throughout the network. In contrast, under strategic substitutes, the same intervention will discourage the individual's neighbors from exerting effort. However, the effect on those neighbors' neighbors will be positive-that is, in the same direction as the effect on the targeted agent. This interplay between spillovers and network structure makes targeting interventions a complex problem.

At the heart of our approach is a particular way to organize the spillover effects in terms of the principal components, or eigenvectors, of the matrix of interactions. Any change in the vector of standalone marginal returns can be expressed in a basis of these principal components. This basis has three special properties: (a) when standalone marginal returns are exogenously changed in the direction of a principal component, the effect is to change equilibrium actions in the same direction; (b) the magnitude of the effect is a multiple of the magnitude of the exogenous change, and the multiplier is determined by an eigenvalue of the network corresponding to that principal component; (c) the principal components are orthogonal, so the effects along various principal components can be treated separately. The three properties we have listed permit us to express the effect of interventions on actions, and on welfare, in a way that facilitates a simple characterization of optimal interventions.

Our main result, Theorem 1, characterizes the optimal intervention in terms of how similar it is to various principal components-or, in other words, how strongly represented various principal components are in it. ${ }^{2}$ Building on this characterization, Corollary 1 describes how the nature of the strategic interaction shapes which principal components figure most prominently in the optimal intervention. The principal components can be ordered by their associated eigenvalues (from high to low). In games of strategic complements, the optimal intervention is, after a suitable normalization, most similar to the first principal component-the vector of individual' eigenvector centralities in the

[^1]network of strategic interactions. It is then progressively less similar to principal components with smaller eigenvalues. In games of strategic substitutes, the order is reversed: the optimal intervention is most similar to the last (lowest-eigenvalue) principal component. The "higher" principal components capture the more global structure of the network: this is important for taking advantage of the aligned feedback effects arising under strategic complementarities. The "lower" principal components capture the local structure of the network: they help the planner to target the intervention so that it does not cause crowding out between adjacent neighbors; this is an important concern when actions are strategic substitutes.

We then turn to the study of simple optimal interventions, that is, ones where the relative intervention on the incentives of each node is determined by a single network statistic of that node, and invariant to other primitives (such as status quo incentives). Propositions 1 and 2 show that, for large enough budgets, the optimal intervention is simple: in games of strategic complements, the optimal intervention vector is proportional to the first principal component, while in games of strategic substitutes, it is proportional to the last one. ${ }^{3}$ Moreover, the network structure determines how large the budget must be for optimal interventions to be simple. In games of strategic complements (substitutes), the important statistic is the gap between the top (bottom) two eigenvalues of the network of strategic interactions. When this gap is large, even at moderate budgets the intervention is simple.

Theorem 1, our characterization of optimal interventions, is derived in a deterministic setting where the planner knows the status quo standalone marginal returns of all individuals. Our methods can also be used to study optimal interventions assuming the planner does not know these returns but knows only their distribution. Propositions 3 and 4 characterize optimal interventions in a stochastic setting. These show that suitable analogues of the main insights extend: the order of the principal components corresponds to how heavily they are represented in the optimal intervention.

We now place the paper in the context of the literature. The intervention problem we study concerns optimal policy in the presence of externalities. Research over the past two decades has deepened our understanding of the empirical structure of networks and the theory of how networks affect strategic behavior. ${ }^{4}$ This has led to the study of how policy design should incorporate information about networks. Network interventions are currently an active subject of research not only in economics but also in related disciplines such as computer science, sociology, and public health. ${ }^{5}$ The main contribution of this paper is methodological. It lies in (i) using the principal components approach to decompose the effect of an intervention on social welfare and (ii) using the structure afforded by this decomposition to characterize optimal interventions. Of special interest is the close

[^2]relation between the strategic structure of the game (whether it features strategic complements or substitutes) and the appropriate principal components to target. ${ }^{6}$

The rest of the paper is organized as follows. Section 2 presents the optimal intervention problem. Section 3 sets out how we apply a principal component decomposition to our game. Section 4 characterizes optimal interventions. Section 5 studies a setting where the planner has incomplete information about agents' standalone marginal returns. Section 6 concludes. The Appendix contains the proofs of the main results-those in Section 4. The Supplemental Material (Galeotti, Golub, and Goyal (2020)) presents the proofs of other results and discusses a number of extensions.

## 2. THE MODEL

We consider a simultaneous-move game among individuals $\mathcal{N}=\{1, \ldots, n\}$, where $n \geq 2$. Individual $i$ chooses an action, $a_{i} \in \mathbb{R}$. The vector of actions is denoted by $\boldsymbol{a} \in \mathbb{R}^{n}$. The payoff to individual $i$ depends on this vector, $\boldsymbol{a}$, the network with adjacency matrix $\boldsymbol{G}$, and other parameters, as described below:

$$
U_{i}(\boldsymbol{a}, \boldsymbol{G})=\underbrace{a_{i}\left(b_{i}+\beta \sum_{j \in \mathcal{N}} g_{i j} a_{j}\right)}_{\text {returns from own action }}-\underbrace{\frac{1}{2} a_{i}^{2}}_{\begin{array}{c}
\text { private costs } \\
\text { of own action }
\end{array}}+\underbrace{P_{i}\left(\boldsymbol{a}_{-i}, \boldsymbol{G}, \boldsymbol{b}\right)}_{\text {pure externalities }} .
$$

The private marginal returns, or benefits, from increasing the action $a_{i}$ depend both on $i$ 's own action, $a_{i}$, and on others' actions. The coefficient $b_{i} \in \mathbb{R}$ corresponds to the part of $i$ 's marginal return that is independent of others' actions, and is thus called $i$ 's standalone marginal return. The contribution of others' actions to $i$ 's marginal return is given by the term $\beta \sum_{j \in \mathcal{N}} g_{i j} a_{j}$. Here $g_{i j} \geq 0$ is a measure of the strength of the interaction between $i$ and $j$; we assume that for every $i \in N, g_{i i}=0$-there are no self-loops in the network $\boldsymbol{G}$. The parameter $\beta$ captures strategic interdependencies. If $\beta>0$, then actions are strategic complements; if $\beta<0$, then actions are strategic substitutes. The function $P_{i}\left(\boldsymbol{a}_{-i}, \boldsymbol{G}, \boldsymbol{b}\right)$ captures pure externalities-that is, spillovers that do not affect best responses. The firstorder condition for individual $i$ 's action to be a best response is

$$
a_{i}=b_{i}+\beta \sum_{j \in \mathcal{N}} g_{i j} a_{j} .
$$

Any Nash equilibrium action profile $\boldsymbol{a}^{*}$ of the game satisfies

$$
[I-\beta G] a^{*}=b
$$

We now make two assumptions about the network and the strength of strategic spillovers. Recall that the spectral radius of a matrix is the maximum of its eigenvalues' absolute values.

Assumption 1: The adjacency matrix $\boldsymbol{G}$ is symmetric. ${ }^{7}$

[^3]Assumption 2: The spectral radius of $\beta \boldsymbol{G}$ is less than 1, ${ }^{8}$ and all eigenvalues of $\boldsymbol{G}$ are distinct. (The latter condition holds generically.)

Assumption 2 ensures that (2) is a necessary and sufficient condition for each individual to be best-responding, and also ensures the uniqueness and stability of the Nash equilibrium. ${ }^{9}$ Under these assumptions, the unique Nash equilibrium of the game can be characterized by

$$
\boldsymbol{a}^{*}=[\boldsymbol{I}-\beta \boldsymbol{G}]^{-1} \boldsymbol{b} .
$$

The utilitarian social welfare at equilibrium is defined as the sum of the equilibrium utilities:

$$
W(\boldsymbol{b}, \boldsymbol{G})=\sum_{i \in \mathcal{N}} U_{i}\left(\boldsymbol{a}^{*}, \boldsymbol{G}\right) .
$$

The planner aims to maximize the utilitarian social welfare at equilibrium by changing a vector of status quo standalone marginal returns $\hat{\boldsymbol{b}}$ to a vector $\boldsymbol{b}$, subject to a budget constraint on the cost of her intervention. The timing is as follows. The planner moves first and chooses her intervention, and then individuals simultaneously choose actions. The planner's incentive-targeting (IT) problem is given by

$$
\begin{array}{ll}
\max _{\boldsymbol{b}} W(\boldsymbol{b}, \boldsymbol{G}) \\
\text { s.t.: } & \boldsymbol{a}^{*}=[\boldsymbol{I}-\beta \boldsymbol{G}]^{-1} \boldsymbol{b} \\
& K(\boldsymbol{b}, \hat{\boldsymbol{b}})=\sum_{i \in \mathcal{N}}\left(b_{i}-\hat{b}_{i}\right)^{2} \leq C,
\end{array}
$$

where $C$ is a given budget. The function $K$ is an adjustment cost of implementing an intervention.

The crucial features of the cost function are that it is separable across individuals and increasing in the magnitude of the change to each individual's incentives. We begin our analysis with the simple functional form given above capturing these features, and examine robustness in the Supplemental Material. In Section OA3.3, we further discuss the form of the adjustment costs and give extensions of the analysis to more general planner cost functions. In Section OA3.4, we examine a setting in which a planner provides monetary payments to individuals that induce them to change their actions, and show that the resulting optimal intervention problem has the same mathematical structure as the one we study in our basic model.

We present two economic applications to illustrate the scope of our model. The first example is a classical investment game, and the second is a game of providing a local public good.

Example 1-The Investment Game: Individual $i$ makes an investment $a_{i}$ at a cost $\frac{1}{2} a_{i}^{2}$. The private marginal return on that investment is $b_{i}+\beta \sum_{j \in \mathcal{N}} g_{i j} a_{j}$, where $b_{i}$ is individual

[^4]$i$ 's standalone marginal return and $\sum_{j \in \mathcal{N}} g_{i j} a_{j}$ is the aggregate local effort. The utility of $i$ is

$$
U_{i}(\boldsymbol{a}, \boldsymbol{G})=a_{i}\left(b_{i}+\beta \sum_{j \in \mathcal{N}} g_{i j} a_{j}\right)-\frac{1}{2} a_{i}^{2} .
$$

The case with $\beta>0$ reflects investment complementarities, as in Ballester, CalvóArmengol, and Zenou (2006). Here, an individual's marginal returns are enhanced when his neighbors work harder; this creates both strategic complementarities and positive externalities. The case of $\beta<0$ corresponds to strategic substitutes and negative externalities; this can be microfounded via a model of competition in a market after the investment decisions $a_{i}$ have been made, as in Goyal and Moraga-Gonzalez (2001). A planner who observes the network of strategic interactions-for instance, which agents work together on joint projects-can intervene by changing levels of monitoring or encouragement relative to a status quo level.

It can be verified that the equilibrium utilities, $U_{i}\left(\boldsymbol{a}^{*}, \boldsymbol{G}\right)$, and the utilitarian social welfare at equilibrium, $W(\boldsymbol{b}, \boldsymbol{G})$, are as follows:

$$
U_{i}\left(\boldsymbol{a}^{*}, \boldsymbol{G}\right)=\frac{1}{2}\left(a_{i}^{*}\right)^{2} \quad \text { and } \quad W(\boldsymbol{b}, \boldsymbol{G})=\frac{1}{2}\left(\boldsymbol{a}^{*}\right)^{\top} \boldsymbol{a}^{*} .
$$

Example 2-Local Public Goods: We next consider a local public goods problem in a framework that follows the work of Bramoullé and Kranton (2007), Galeotti and Goyal (2010), and Allouch (2015, 2017). In a local public goods problem, each agent makes a costly contribution, which brings her closer to an ideal level of public goods but also raises the levels enjoyed by her neighbors. Examples include (i) contributions to improve physical neighborhoods, such as residents clearing snow; ${ }^{10}$ (ii) knowledge workers acquiring non-rivalrous information (e.g., about job applicants) that can be shared with colleagues. In example (i), the network governing spillovers is given by physical proximity, while in example (ii), it is given by organizational overlap. We now elaborate on the nature of initial incentives and the interventions in the context of example (i). Agents receive some level of municipal services at the status quo. They augment it with their own effort, and benefit (with a discount) from the efforts contributed by neighbors. A planner (say, a city councilor) who observes the network structure of physical proximity among houses can intervene to change the status quo allocation of services, tailoring it to improve incentives.

Formally, suppose that if each $i$ contributes effort $a_{i}$ to the public good, then the amount of public good $i$ experiences is

$$
x_{i}=\tilde{b}_{i}+a_{i}+\tilde{\beta} \sum_{j \in \mathcal{N}} g_{i j} a_{j}
$$

where $0<\tilde{\beta}<1$. The utility of $i$ is

$$
U_{i}(\boldsymbol{a}, \boldsymbol{G})=-\frac{1}{2}\left(\tau-x_{i}\right)^{2}-\frac{1}{2} a_{i}^{2},
$$

where $\tilde{b}_{i}<\tau$.

[^5]We now connect these formulas to the motivating descriptions. The optimal level of public good in the absence of any costs is $\tau$; this can be thought of as the maximum that can be provided. Individual $i$ has access to a base level $\tilde{b}_{i}$ of the public good. Each agent can expend costly effort, $a_{i}$, to augment this base level to $\tilde{b}_{i}+a_{i}$. If $i$ 's neighbor $j$ expends effort, $a_{j}$, then $i$ has access to an additional $\tilde{\beta} g_{i j} a_{j}$ units of the public good, where $\tilde{\beta}<1$.

This is a game of strategic substitutes and positive externalities. Performing the change of variables $b_{i}=\left[\tau-b_{i}\right] / 2$ and $\beta=-\tilde{\beta} / 2$ (with the status quo equal to $\hat{b}_{i}=\left[\tau-\tilde{b}_{i}\right] / 2$ ) yields a best-response structure exactly as in condition (2). The aggregate equilibrium utility is $W(\boldsymbol{b}, \boldsymbol{G})=-\left(\boldsymbol{a}^{*}\right)^{\top} \boldsymbol{a}^{*}$.

All the settings discussed in Examples 1 and 2 share a technically convenient property:
Property A: The aggregate equilibrium utility is proportional to the sum of the squares of the equilibrium actions, that is, $W(\boldsymbol{b}, \boldsymbol{G})=w \cdot\left(\boldsymbol{a}^{*}\right)^{\top} \boldsymbol{a}^{*}$ for some $w \in \mathbb{R}$, where $\boldsymbol{a}^{*}$ is the Nash equilibrium action profile.

Supplemental Material Section OA2.2 discusses a network beauty contest game inspired by Morris and Shin (2002) and Angeletos and Pavan (2007) which also satisfies this property. While Property A facilitates analysis, it is not essential. Supplemental Material Section OA3.1 extends the analysis to cover important cases where this property does not hold.

## 3. PRINCIPAL COMPONENTS

This section introduces a basis for the space of standalone marginal returns and actions in which, under our assumptions on $\boldsymbol{G}$, strategic effects and the planner's objective both take a simple form.

FACT 1: If $\boldsymbol{G}$ satisfies Assumption 1 , then $\boldsymbol{G}=\boldsymbol{U} \boldsymbol{\Lambda} \boldsymbol{U}^{\top}$, where:

1. $\boldsymbol{\Lambda}$ is an $n \times n$ diagonal matrix whose diagonal entries $\Lambda_{\ell \ell}=\lambda_{\ell}$ are the eigenvalues of $\boldsymbol{G}$ (which are real numbers), ordered from greatest to least: $\lambda_{1} \geq \lambda_{2} \geq \cdots \geq \lambda_{n}$.
2. $\boldsymbol{U}$ is an orthogonal matrix. The $\ell$ th column of $\boldsymbol{U}$, which we call $\boldsymbol{u}^{\ell}$, is a real eigenvector of $\boldsymbol{G}$, namely, the eigenvector associated to the eigenvalue $\lambda_{\ell}$, which is normalized so that $\left\|\boldsymbol{u}^{\ell}\right\|=1$ (in the Euclidean norm).

For generic $\boldsymbol{G}$, the decomposition is uniquely determined, except that any column of $\boldsymbol{U}$ is determined only up to multiplication by -1 .

An important interpretation of this diagonalization is as a decomposition into principal components. First, consider the symmetric rank-one matrix that best approximates $\boldsymbol{G}$ in the squared-error sense-equivalently, the vector $\boldsymbol{u}$ such that

$$
\sum_{i, j \in \mathcal{N}}\left(g_{i j}-u_{i} u_{j}\right)^{2}
$$

is minimized. The minimizer turns out to be a scaling of the eigenvector $\boldsymbol{u}^{1}$. Now, if we consider the "residual" matrix $\boldsymbol{G}^{(2)}=\boldsymbol{G}-\boldsymbol{u}^{1}\left(\boldsymbol{u}^{1}\right)^{\top}$, we can perform the same type of decomposition on $\boldsymbol{G}^{(2)}$ and obtain the second eigenvector $\boldsymbol{u}^{2}$ as the best rank-one approximation. Proceeding further in this way gives a sequence of vectors that constitute an

![](/documents/beda4dca-f4a7-4264-a3bc-78fa06685dd1/images/image_001.jpg)
Figure 1.-(Top) Eigenvectors 2, 4, 6. (Bottom) Eigenvectors 10, 12, 14. Node shading represents the sign of the entry, with the lighter shading (green) indicating a positive entry and the darker shading (red) indicating a negative entry. Node area is proportional to the magnitude of the entry.

orthonormal basis. At each step, the next vector generates the rank-one matrix that "best summarizes" the remaining structure in the matrix $\boldsymbol{G} .{ }^{11}$

Figure 1 illustrates some eigenvectors/principal components of a circle network with 14 nodes, where links all have equal weight given by 1 . For each eigenvector, the shading of a node indicates the sign of the entry corresponding to that node in that eigenvector, while the size of a node indicates the absolute value of that entry. ${ }^{12}$ A general feature worth noting is that the entries of the top eigenvectors (with smaller values of $\ell$ ) are similar among neighboring nodes, while the bottom eigenvectors (with larger values of $\ell$ ) tend to be negatively correlated among neighboring nodes. ${ }^{13}$

### 3.1. Analysis of the Game Using Principal Components

For any vector $\boldsymbol{z} \in \mathbb{R}^{n}$, let $\underline{\boldsymbol{z}}=\boldsymbol{U}^{\top} \boldsymbol{z}$. We will refer to $\underline{\boldsymbol{z}}_{\ell}$ as the projection of $\boldsymbol{z}$ onto the $\ell$ th principal component, or the magnitude of $\boldsymbol{z}$ in that component. Substituting the expression $\boldsymbol{G}=\boldsymbol{U} \boldsymbol{\Lambda} \boldsymbol{U}^{\top}$ into equation (2), which characterizes equilibrium, we obtain

$$
\left[I-\beta \boldsymbol{U} \boldsymbol{\Lambda} \boldsymbol{U}^{\top}\right] a^{*}=b .
$$

Multiplying both sides of this equation by $\boldsymbol{U}^{\top}$ gives us an analogue of (3) characterizing the solution of the game:

$$
[\boldsymbol{I}-\beta \boldsymbol{\Lambda}] \underline{a}^{*}=\underline{b} \quad \Longleftrightarrow \quad \underline{a}^{*}=[\boldsymbol{I}-\beta \boldsymbol{\Lambda}]^{-1} \underline{b} .
$$

This system is diagonal, and the $\ell$ th diagonal entry of $[\boldsymbol{I}-\boldsymbol{\beta} \boldsymbol{\Lambda}]^{-1}$ is $\frac{1}{1-\beta \lambda_{\ell}}$. Hence, for every $\ell \in\{1,2, \ldots, n\}$,

$$
\underline{a}_{\ell}^{*}=\frac{1}{1-\beta \lambda_{\ell}} \underline{b}_{\ell} .
$$

[^6]The principal components of $\boldsymbol{G}$ constitute a basis in which strategic effects are easily described. The equilibrium action $\underline{a}_{\ell}^{*}$ in the $\ell$ th principal component of $\boldsymbol{G}$ is the product of an amplification factor (determined by the strategic parameter $\beta$ and the eigenvalue $\lambda_{\ell}$ ) and $\underline{b}_{\ell}$, which is simply the projection of $\boldsymbol{b}$ onto that principal component. Under Assumption 2, for all $\ell$ we have $1-\beta \lambda_{\ell}>0 .^{14}$ Moreover, when $\beta>0(\beta<0)$, the amplification factor is decreasing (increasing) in $\ell$.

We can also use (4) to give a formula for equilibrium actions in the original coordinates:

$$
a_{i}^{*}=\sum_{\ell=1}^{n} \frac{1}{1-\beta \lambda_{\ell}} u_{i}^{\ell} \underline{b}_{\ell} .
$$

We close with a definition that will allow us to describe optimal interventions in terms of a standard measure of their similarity to various principal components.

DEFINITION 1: The cosine similarity of two nonzero vectors $\boldsymbol{y}$ and $\boldsymbol{z}$ is $\rho(\boldsymbol{y}, \boldsymbol{z})=\frac{\boldsymbol{y} \cdot \boldsymbol{z}}{\|\boldsymbol{y}\|}$.
This is the cosine of the angle between the two vectors in a plane determined by $\boldsymbol{y}$ and $z$. When $\rho(\boldsymbol{y}, \boldsymbol{z})=1$, the vector $\boldsymbol{z}$ is a positive scaling of $\boldsymbol{y}$. When $\rho(\boldsymbol{y}, \boldsymbol{z})=0$, the vectors $\boldsymbol{y}$ and $\boldsymbol{z}$ are orthogonal. When $\rho(\boldsymbol{y}, \boldsymbol{z})=-1$, the vector $\boldsymbol{z}$ is a negative scaling of $\boldsymbol{y}$.

## 4. OPTIMAL INTERVENTIONS

This section develops a characterization of optimal interventions in terms of the principal components and studies their properties.

We begin by dispensing with a straightforward case of the planner's problem. Recall that under Property A, the planner's payoff as a function of the equilibrium actions $\boldsymbol{a}^{*}$ is $W(\boldsymbol{b}, \boldsymbol{G})=w \cdot\left(\boldsymbol{a}^{*}\right)^{\top} \boldsymbol{a}^{*}$. If $w<0$, the planner wishes to minimize the sum of the squares of the equilibrium actions. In this case, when the budget is large enough—that is, $C \geq\|\hat{\boldsymbol{b}}\|^{2}$ — the planner can allocate resources to ensure that individuals have a zero target action by setting $b_{i}=0$ for all $i$. It follows from the best-response equations that all individuals choose action 0 in equilibrium, and so the planner achieves the first-best. ${ }^{15}$ The next assumption rules out the case in which the planner's bliss point can be achieved, ensuring that there is an interesting optimization problem.

Assumption 3: Either $w<0$ and $C<\|\hat{\boldsymbol{b}}\|$, or $w>0$. Moreover, $\underline{\hat{b}}_{\ell} \neq 0$ for each $\ell$.
The last part of the assumption is technical; it holds for generic status quo vectors $\hat{\boldsymbol{b}}$ (or generic $\boldsymbol{G}$ fixing a status quo vector) and faciliates a description of the optimal intervention in terms of similarity to the status quo vector.

Let $\boldsymbol{b}^{*}$ solve the incentive-targeting problem (IT), and let $\boldsymbol{y}^{*}=\boldsymbol{b}^{*}-\hat{\boldsymbol{b}}$ be the vector of changes in individuals' standalone marginal returns at the optimal intervention. Furthermore, let

$$
\alpha_{\ell}=\frac{1}{\left(1-\beta \lambda_{\ell}\right)^{2}}
$$

[^7]and note that $\underline{a}_{\ell}^{*}=\sqrt{\alpha_{\ell}} \underline{b}_{\ell}$ is the equilibrium action in the $\ell$ th principal component of $\boldsymbol{G}$ (see equation (4)).

Theorem 1: Suppose Assumptions 1-3 hold and the network game satisfies Property A. At the optimal intervention, the cosine similarity between $\boldsymbol{y}^{*}$ and principal component $\boldsymbol{u}^{\ell}(\boldsymbol{G})$ satisfies the following proportionality:

$$
\rho\left(y^{*}, \boldsymbol{u}^{\ell}(\boldsymbol{G})\right) \propto \rho\left(\hat{\boldsymbol{b}}, \boldsymbol{u}^{\ell}(\boldsymbol{G})\right) \frac{w \alpha_{\ell}}{\mu-w \alpha_{\ell}}, \quad \ell=1,2, \ldots, n,
$$

where $\mu$, the shadow price of the planner's budget, is uniquely determined as the solution to

$$
\sum_{\ell=1}^{n}\left(\frac{w \alpha_{\ell}}{\mu-w \alpha_{\ell}}\right)^{2} \hat{b}_{\ell}^{2}=C
$$

and satisfies $\mu>w \alpha_{\ell}$ for all $\ell$, so that all denominators are positive.
We briefly sketch the main argument here and interpret the quantities in the formula. Define $x_{\ell}=\left(\underline{b}_{\ell}-\underline{\hat{b}}_{\ell}\right) / \underline{\hat{b}}_{\ell}$ as the change in $\underline{b}_{\ell}$, relative to $\underline{\hat{b}}_{\ell}$. By rewriting the principal's objective $W(\boldsymbol{b}, \boldsymbol{G})$ and budget constraints in terms of principal components and plugging in the equilibrium condition (4), we can rewrite the maximization problem (IT) as

$$
\max _{x} \sum_{\ell=1}^{n} w \alpha_{\ell}\left(1+x_{\ell}\right)^{2} \hat{\underline{b}}_{\ell}^{2} \quad \text { s.t. } \quad \sum_{\ell=1}^{n} \hat{\underline{b}}_{\ell}^{2} x_{\ell}^{2} \leq C .
$$

If the planner allocates a marginal unit of the budget to changing $x_{\ell}$, the condition for equality of the marginal return and marginal cost (recalling that $\mu$ is the multiplier on the budget constraint) is

$$
\underbrace{2 \hat{b}_{\ell}^{2} \cdot w \alpha_{\ell}\left(1+x_{\ell}\right)}_{\text {marginal return }}=\underbrace{2 \hat{b}_{\ell}^{2} \cdot \mu x_{\ell}}_{\text {marginal cost }} .
$$

It follows that $\frac{w \alpha_{\ell}}{\mu-w \alpha_{\ell}}$ is exactly the value of $x_{\ell}$ at which the marginal return and the marginal cost are equalized. ${ }^{16}$ Rewriting $x_{\ell}$ in terms of cosine similarity, that equality implies

$$
\frac{w \alpha_{\ell}}{\mu-w \alpha_{\ell}}=x_{\ell}^{*}=\frac{\left\|\boldsymbol{y}^{*}\right\| \rho\left(\boldsymbol{y}^{*}, \boldsymbol{u}^{\ell}(\boldsymbol{G})\right)}{\|\hat{\boldsymbol{b}}\| \rho\left(\hat{\boldsymbol{b}}, \boldsymbol{u}^{\ell}(\boldsymbol{G})\right)} .
$$

Rearranging this yields the proportionality expression (5) in the theorem. The Lagrange multiplier $\mu$ is determined by solving (6). Now, given $\mu$, the similarities $\rho\left(\boldsymbol{y}^{*}, \boldsymbol{u}^{\ell}(\boldsymbol{G})\right)$ determine the direction of the optimal intervention $\boldsymbol{y}^{*}$. The magnitude of the intervention is found by exhausting the budget. Thus, Theorem 1 entails a full characterization of the optimal intervention.

[^8]Next, we discuss the formula for the similarities given in expression (5). The similarity between $\boldsymbol{y}^{*}$ and $\boldsymbol{u}^{\ell}(\boldsymbol{G})$ measures the extent to which principal component $\boldsymbol{u}^{\ell}(\boldsymbol{G})$ is represented in the optimal intervention $\boldsymbol{y}^{*}$. Equation (5) tells us that this is proportional to two factors. The first factor, $\rho\left(\hat{\boldsymbol{b}}, \boldsymbol{u}^{\ell}(\boldsymbol{G})\right)$, measures the similarity between the $\ell$ th principal component and the status quo vector $\hat{\boldsymbol{b}}$. This factor summarizes a status quo effect: how much the initial condition influences the optimal intervention for a given budget. The intuition here is that if a given principal component is strongly represented in the status quo vector of standalone incentives, then-because of the convexity of welfare in the principal component basis-changes in that dimension have a particularly large effect.

The second factor, $\frac{w \alpha_{\ell}}{\mu-w \alpha_{\ell}}$, is determined by two quantities: the eigenvalue corresponding to $\boldsymbol{u}^{\ell}(\boldsymbol{G})$ (via $\alpha_{\ell}=\frac{1}{\left(1-\beta \lambda_{\ell}\right)^{2}}$ ), and the budget $C$ (via the shadow price $\mu$ ). To focus on this second factor, $\frac{w \alpha_{\ell}}{\mu-w \alpha_{\ell}}$, we define the similarity ratio

$$
r_{\ell}^{*}=\frac{\rho\left(y^{*}, \boldsymbol{u}^{\ell}(\boldsymbol{G})\right)}{\rho\left(\hat{\boldsymbol{b}}, \boldsymbol{u}^{\ell}(\boldsymbol{G})\right)} .
$$

Theorem 1 shows that, as we vary $\ell$, the similarity ratio $r_{\ell}^{*}$ is proportional to $\frac{w \alpha_{\ell}}{\mu-w \alpha_{\ell}}$. It follows that the similarity ratio is greater, in absolute value, for the principal components $\ell$ with greater $\alpha_{\ell}$. Intuitively, those are the components where the optimal intervention makes the largest change relative to the status quo profile of incentives. The ordering of the $r_{\ell}^{*}$ corresponds to the eigenvalues in a way that depends on the nature of strategic spillovers:

Corollary 1: Suppose Assumptions 1-3 hold and the network game satisfies Property A. If the game is one of strategic complements ( $\beta>0$ ), then $\left|r_{\ell}^{*}\right|$ is decreasing in $\ell$; if the game is one of strategic substitutes ( $\beta<0$ ), then $\left|r_{\ell}^{*}\right|$ is increasing in $\ell$.

In some problems, there may be a nonnegativity constraint on actions, in addition to the constraints in problem (IT). As long as the status quo actions $\hat{\boldsymbol{b}}$ are positive, this constraint will be respected for all $C$ less than some $\hat{C}$, and so our approach will give information about the relative effects on various components for interventions that are not too large.

### 4.1. Small and Large Budgets

The optimal intervention takes especially simple forms in the cases of small and large budgets. From equation (6), we can deduce that the shadow price $\mu$ is decreasing in $C$. For $w>0$, it follows that an increase in $C$ raises $\frac{w \alpha_{\ell}}{\mu-w \alpha_{\ell}}$. Moreover, the sequence of similarity ratios becomes "steeper" as we increase $C$, in the following sense: if $w>0$, for all $\ell, \ell^{\prime}$ such that $\alpha_{\ell}>\alpha_{\ell^{\prime}}$, we have that $r_{\ell}^{*} / r_{\ell^{\prime}}^{*}$ is increasing in $C$. ${ }^{17}$

Proposition 1: Suppose Assumptions 1-3 hold and the network game satisfies Property A. Then the following hold:

1. As $C \rightarrow 0$, in the optimal intervention, $\frac{r_{\ell}^{*}}{r_{\ell^{\prime}}^{*}} \rightarrow \frac{\alpha_{\ell}}{\alpha_{\ell^{\prime}}}$.
2. As $C \rightarrow \infty$, in the optimal intervention:
   [^9]2a. If $\beta>0$ (the game features strategic complements), then the similarity of $\boldsymbol{y}^{*}$ and the first principal component of the network tends to $1: \rho\left(\boldsymbol{y}^{*}, \boldsymbol{u}^{1}(\boldsymbol{G})\right) \rightarrow 1$.
   2b. If $\beta<0$ (the game features strategic substitutes), then the similarity of $\boldsymbol{y}^{*}$ and the last principal component of the network tends to $1: \rho\left(\boldsymbol{y}^{*}, \boldsymbol{u}^{n}(\boldsymbol{G})\right) \rightarrow 1$.

This result can be understood by recalling equation (5) in Theorem 1. First, consider the case of small $C$. When the planner's budget becomes small, the shadow price $\mu$ tends to $\infty$. ${ }^{18}$ Equation (5) then implies that the similarity ratio $r_{\ell}^{*}$ of the $\ell$ th principal component (recall (7)) becomes proportional to $\alpha_{\ell}$. Turning now to the case where $C$ grows large, the shadow price converges to $w \alpha_{1}$ if $\beta>0$, and to $w \alpha_{n}$ if $\beta<0$ (by equation (6)). Plugging this into equation (5), we find that in the case of strategic complements, the optimal intervention shifts individuals' standalone marginal returns (very nearly) in proportion to the first principal component of $\boldsymbol{G}$, so that $\boldsymbol{y}^{*} \rightarrow \sqrt{C} \boldsymbol{u}^{1}(\boldsymbol{G})$. In the case of strategic substitutes, on the other hand, the planner changes individuals' standalone marginal returns (very nearly) in proportion to the last principal component, namely, $\boldsymbol{y}^{\boldsymbol{*}} \rightarrow \sqrt{C} \boldsymbol{u}^{\boldsymbol{n}}(\boldsymbol{G}) .^{19}$

Figure 2 depicts the optimal intervention in an example where the budget is large. We consider an 11-node undirected network with binary links containing two hubs, $L_{0}$ and $R_{0}$, that are connected by an intermediate node $M$; the network is depicted in Figure 2(A). The numbers next to the nodes are the status quo standalone marginal returns; the budget is set to $C=500 .{ }^{20}$ Payoffs are as in Example 1. For the case of strategic complements, we set $\beta=0.1$, and for strategic substitutes, we set $\beta=-0.1$. Assumptions 1 and 2 are satisfied and Property A holds. The top-left of Figure 2(B) illustrates the first eigenvector, and the top-right depicts the optimal intervention in a game with strategic complements. The bottom-left of Figure 2(B) illustrates the last eigenvector, and the bottom-right depicts the optimal intervention when the game has strategic substitutes. The node size represents the size of the intervention, $\left|b_{i}^{*}-\hat{b}_{i}\right|$; node shading represents the sign of the

![](/documents/beda4dca-f4a7-4264-a3bc-78fa06685dd1/images/image_002.jpg)
FIGURE 2.-An example of optimal interventions with large budgets.

[^10]intervention, with the lighter shading (green) indicating a positive intervention and the darker shading (red) indicating a negative intervention.

In line with part 2 of Proposition 1, for large $C$, the optimal intervention is guided by the "main" component of the network. Under strategic complements, this is the first (largesteigenvalue) eigenvector of the network, whose entries are individuals' eigenvector centralities. ${ }^{21}$ Intuitively, by increasing the standalone marginal return of each individual in proportion to his eigenvector centrality, the planner targets the individuals in proportion to their global contributions to strategic feedbacks, and this is welfare-maximizing.

Under strategic substitutes, optimal targeting is determined by the last eigenvector of the network, corresponding to its smallest eigenvalue. This network component contains information about the local structure of the network: it determines a way to partition the set of nodes into two sets so that most of the links are across individuals in different sets. ${ }^{22}$ The optimal intervention increases the standalone marginal returns of all individuals in one set and decreases those of individuals in the other set. The planner wishes to target neighboring nodes asymmetrically, as this reduces crowding-out effects that occur due to the strategic substitutes property.

### 4.2. When Are Interventions Simple?

We have just seen examples illustrating how, with large budgets, the intervention is approximately simple in a certain sense: proportional to just one principal component. After formalizing a suitable notion of simplicity in our setting, the final result in this section characterizes how large the budget must be for such an approximation to be accurate.

Definition 2-Simple Interventions: An intervention is simple if, for all $i \in \mathcal{N}$,

- $b_{i}-\hat{b}_{i}=\sqrt{C} u_{i}^{1}$ when the game has the strategic complements property ( $\beta>0$ ),
- $b_{i}-\hat{b}_{i}=\sqrt{C} u_{i}^{n}$ when the game has the strategic substitutes property ( $\beta<0$ ).

Such an intervention is called simple because the intervention on each node is-up to a common scaling-determined by a single number that depends only on the network (via its eigenvectors), and not on any other details such as the status quo incentives. ${ }^{23}$ Let $W^{*}$ be the aggregate utility under the optimal intervention, and let $W^{s}$ be the aggregate utility under the simple intervention.

Proposition 2: Suppose $w>0$, Assumptions 1 and 2 hold, and the network game satisfies Property A.

1. If the game has the strategic complements property, $\beta>0$, then for any $\epsilon>0$, if $C> \frac{2\|\hat{\boldsymbol{b}}\|^{2}}{\epsilon}\left(\frac{\alpha_{2}}{\alpha_{1}-\alpha_{2}}\right)^{2}$, then $W^{*} / W^{s}<1+\epsilon$ and $\rho\left(\boldsymbol{y}^{*}, \sqrt{C} \boldsymbol{u}^{1}\right)>\sqrt{1-\epsilon}$.
2. If the game has the strategic substitutes property, $\beta<0$, then for any $\epsilon>0$, if $C> \frac{2\|\hat{\boldsymbol{b}}\|^{2}}{\epsilon}\left(\frac{\alpha_{n-1}}{\alpha_{n}-\alpha_{n-1}}\right)^{2}$, then $W^{*} / W^{s}<1+\epsilon$ and $\rho\left(\boldsymbol{y}^{*}, \sqrt{C} \boldsymbol{u}^{n}\right)>\sqrt{1-\epsilon}$.
   [^11]Proposition 2 gives a condition on the size of the budget beyond which (a) simple interventions achieve most of the optimal welfare and (b) the optimal intervention is very similar to the simple intervention. This bound depends on the status quo standalone marginal returns and on the structure of the network via $\frac{\alpha_{2}}{\alpha_{1}-\alpha_{2}}$ (or a corresponding factor for "bottom" $\alpha$ 's).

We first discuss the dependence of the bound on the status quo marginal returns. Observe that the first term on the right-hand side of the inequality for $C$ is proportional to the squared norm of $\hat{\boldsymbol{b}}$. This inequality is therefore easier to satisfy when this vector has a smaller norm. The inequality is harder to satisfy when these marginal returns are large and/or heterogeneous. ${ }^{24}$

Next, consider the role of the network. Recall that $\alpha_{\ell}=\left(1-\beta \lambda_{\ell}\right)^{-2}$; thus if $\beta>0$, the term $\alpha_{2} /\left(\alpha_{1}-\alpha_{2}\right)$ of the inequality is large when $\lambda_{1}-\lambda_{2}$, the "spectral gap" of the graph, is small. If $\beta<0$, then the term $\alpha_{n-1} /\left(\alpha_{n-1}-\alpha_{n}\right)$ is large when the difference $\lambda_{n-1}-\lambda_{n}$, which we call the "bottom gap," is small.

We now examine what network features affect these gaps, and illustrate with examples, depicted in Figure 3. The obstacle to the existence of simple optimal interventions is a strong dependence on the status quo standalone marginal returns. This dependence will be strong when two different principal components in the network offer the potential for similar amplification of an intervention. Which of these principal components receives the planner's focus will depend strongly on the status quo. In such networks, interventions will not be simple unless budgets are very large relative to status quo incentives. The

![](/documents/beda4dca-f4a7-4264-a3bc-78fa06685dd1/images/image_003.jpg)
Figure 3.-Spectral gap, bottom gap, and optimal interventions.

[^12]implication of Proposition 2 is that this sensitivity occurs when the appropriate gap in eigenvalues (spectral gap or bottom gap) is small. Figure 3 illustrates the role of the network structure in shaping how the optimal intervention converges to the simple one (as $C$ increases). Under strategic complements, a large spectral gap ensures fast convergence. Under strategic substitutes, a large bottom gap ensures fast convergence.

We now describe which more directly visible properties of network topology correspond to small and large spectral gaps. First, consider the case of strategic complements. A standard fact is that the two largest eigenvalues can be expressed as follows:

$$
\lambda_{1}=\max _{\boldsymbol{u}:\|\boldsymbol{u}\|=1} \sum_{i, j \in \mathcal{N}} g_{i j} u_{i} u_{j}, \quad \lambda_{2}=\max _{\substack{\boldsymbol{u}:\|\boldsymbol{u}\|=1 \\ \boldsymbol{u} \cdot \boldsymbol{u}^{1}=0}} \sum_{i, j \in \mathcal{N}} g_{i j} u_{i} u_{j} .
$$

Moreover, the eigenvector $\boldsymbol{u}^{1}$ is a maximizer of the first problem, while $\boldsymbol{u}^{2}$ is a maximizer of the second; these are uniquely determined under Assumption 2. By the PerronFrobenius theorem, the first eigenvector, $\boldsymbol{u}^{1}$, assigns the same sign-say, positive-to all nodes in the network. Then the eigenvector $\boldsymbol{u}^{2}$ must clearly assign negative values to some of the nodes (as it is orthogonal to $\boldsymbol{u}^{1}$ ). In the network on the left side of Figure 3(A), any such assignment will result in many adjacent nodes having opposite-sign entries of $\boldsymbol{u}^{2}$; as a result, many terms in the expression for $\lambda_{2}$ will be negative, and $\lambda_{2}$ will be considerably smaller than $\lambda_{1}$, leading to a large spectral gap. In the network on the right side of Figure 3(A), $\boldsymbol{u}^{2}$ turns out to have positive-sign entries for nodes in one community and negative-sign entries for nodes in the other community. Because there are few edges between the communities, $\lambda_{2}$ turns out to be almost as large as $\lambda_{1}$. This yields a small spectral gap. These observations illustrate that the spectral gap is large when the network is "cohesive," and small when the network is, in contrast, divisible into nearly-disconnected communities. ${ }^{25}$ In light of this interpretation, our results imply that highly cohesive networks admit near-optimal interventions that are simple.

Turning next to strategic substitutes, recall that the smallest two eigenvalues, $\lambda_{n}$ and $\lambda_{n-1}$, can be written as follows:

$$
\lambda_{n}=\min _{\boldsymbol{u}:\|\boldsymbol{u}\|=1} \sum_{i, j \in \mathcal{N}} g_{i j} u_{i} u_{j}, \quad \lambda_{n-1}=\min _{\substack{\boldsymbol{u}:\|\boldsymbol{u}\|=1 \\ \boldsymbol{u} \cdot \boldsymbol{u}^{n}=0}} \sum_{i, j \in \mathcal{N}} g_{i j} u_{i} u_{j} .
$$

Moreover, the eigenvector $\boldsymbol{u}^{n}$ is a maximizer of the first problem, while $\boldsymbol{u}^{n-1}$ is a maximizer of the second; these are uniquely determined under Assumption 2. This tells us that $\lambda_{n}$ is low ${ }^{26}$ when the eigenvector $\boldsymbol{u}^{n}=\arg \min _{\boldsymbol{u}:\|\boldsymbol{u}\|=1} \sum_{i, j \in \mathcal{N}} g_{i j} u_{i} u_{j}$ (corresponding to $\lambda_{n}$ ) assigns opposite signs to most pairs of adjacent nodes. In other words, the last eigenvalue is small when nodes can be partitioned into two sets and most of the connections are across sets. Thus, $\lambda_{n}$ is minimized in a bipartite graph. The second-smallest eigenvalue of $\boldsymbol{G}$ reflects the extent to which the next-best eigenvector (orthogonal to $\boldsymbol{u}^{n}$ ) is good at solving the same minimization problem. Hence, the bottom gap of $\boldsymbol{G}$ is small when there are two orthogonal ways to partition the network into two sets so that, either way, the "quality" of the bipartition, as measured by $\sum_{i, j \in \mathcal{N}} g_{i j} u_{i} u_{j}$, is similar.

[^13]We illustrate part 2 of Proposition 2 with a comparison of the two graphs in Figure 3(C). The left-hand graph is bipartite: the last eigenvalue is $\lambda_{n}=-3$ and the second-last eigenvalue is $\lambda_{n-1}=-1.64$. In contrast, the graph on the right of Figure 3(C) has a bottom eigenvalue $\lambda_{n}=-2.62$, and a second-lowest eigenvalue of $\lambda_{n-1}=-2.30$. This yields a much smaller bottom gap. ${ }^{27}$ This difference in bottom gaps is reflected in the nature of optimal interventions shown in Figure 3(D). In the graph with large bottom gap, the optimal intervention puts most of its weight on the eigenvector $\boldsymbol{u}^{n}$ even for relatively small budgets. To achieve a similar convergence to simplicity requires a much larger budget when the bottom gap is small: the second-smallest eigenvector $\boldsymbol{u}^{n-1}$ receives substantial weight even for fairly large values of the budget $C$.

We conclude by noting the influence of the status quo standalone marginal returns in shaping optimal interventions for small budgets. For a small budget $C$, the cosine similarity of the optimal intervention for non-main network components can be higher than the one for the main component. This is true when the status quo $\hat{\boldsymbol{b}}$ is similar to some of the non-main network components; see Figures 3(B) and Figure 3(D).

## 5. INCOMPLETE INFORMATION

In the basic model, we assumed that the planner knows the standalone marginal returns of every individual. This section extends the analysis to settings where the planner does not know these parameters. As before, we focus on network games that satisfy Property A.

Formally, fix a probability space ( $\Omega, \mathcal{F}, \mathbb{P}$ ). The planner's probability distribution over states is given by $\mathbb{P}$. The planner has control over the random vector (r.v.) $\mathcal{B}$-that is, a function $\mathcal{B}: \Omega \rightarrow \mathbb{R}^{n}$. The cost of the intervention depends on the choice of $\mathcal{B}$. There is a function $K$ that gives the cost $K(\mathcal{B})$ of implementing the random variable $\mathcal{B} .^{28} \mathrm{~A}$ realization of the random vector is denoted by $\boldsymbol{b}$. This realization is common knowledge among individuals when they choose their actions. Thus, the game individuals play is one of complete information. ${ }^{29}$

We solve the following incomplete-information intervention problem:

$$
\begin{array}{cl}
\text { choose r.v. } \mathcal{B} \text { to maximize } \mathbb{E}[W(\boldsymbol{b} ; \boldsymbol{G})] \\
\text { s.t. } & {[\boldsymbol{I}-\beta \boldsymbol{G}] \boldsymbol{a}^{*}=\boldsymbol{b},} \\
& K(\mathcal{B}) \leq C .
\end{array}
$$

Note that the intervention problem (IT) under complete information is the special case of a degenerate r.v. $\mathcal{B}$ : one in which the planner knows the vector of standalone marginal returns exactly and implements a deterministic adjustment relative to it.

To guide our modeling of the cost of intervention, we now examine the features of the distribution of $\mathcal{B}$ that matter for aggregate welfare. For network games that satisfy

[^14]Property A, we can write

$$
\mathbb{E}[W(\boldsymbol{b} ; \boldsymbol{G})]=w \mathbb{E}\left[\left(\boldsymbol{a}^{*}\right)^{\top} \boldsymbol{a}^{*}\right]=w \mathbb{E}\left[\left(\underline{\boldsymbol{a}}^{\top}\right)^{*}\left(\underline{\boldsymbol{a}}^{*}\right)\right]=w \sum_{\ell=1}^{n} \alpha_{\ell}\left(\mathbb{E}\left[\underline{\boldsymbol{b}}_{\ell}\right]^{2}+\operatorname{Var}\left[\underline{\boldsymbol{b}}_{\ell}\right]\right) .
$$

Note the change from the ordinary to the principal component basis in the second step. In words, welfare is determined by the mean and variance of the realized components $\underline{b}_{\ell}$; these in turn are determined by the first and second moments of the chosen random variable $\mathcal{B}$. In view of this, we will consider intervention problems where the planner can modify the mean and the covariance matrix of $\mathcal{B}$, and the cost of intervention depends only on these modifications. ${ }^{30}$

### 5.1. Mean Shifts

We first consider an intervention where there is an arbitrarily distributed vector of status quo standalone marginal returns and the planner's intervention shifts it in a deterministic way. Formally, fix a random variable $\hat{\mathcal{B}}$, called the status quo, with typical realization $\hat{\boldsymbol{b}}$. The planner's policy is given by $\boldsymbol{b}=\hat{\boldsymbol{b}}+\boldsymbol{y}$, where $\boldsymbol{y} \in \mathbb{R}^{n}$ is a deterministic vector. We denote the corresponding random variable by $\mathcal{B}_{y}$. In terms of interpretation, note that implementing this policy does not require knowing $\hat{\boldsymbol{b}}$ as long as the planner has an instrument that shifts incentives.

Assumption 4: The cost of implementing r.v. $\mathcal{B}_{y}$ is

$$
K\left(\mathcal{B}_{y}\right)=\sum_{i \in \mathcal{N}} y_{i}^{2},
$$

and $K(\mathcal{B})$ is $\infty$ for any other random variable.
In contrast to the analysis of Theorem 1 , the vector $\hat{\boldsymbol{b}}$ is a random variable. But we take the analogue of the cost function used there, noting that in the deterministic setting (see (IT)), this formula held with $\boldsymbol{y}=\boldsymbol{b}-\hat{\boldsymbol{b}}$.

Proposition 3: Consider problem (IT-G), with the cost of intervention satisfying Assumption 4. Suppose Assumptions 1 and 2 hold and the network game satisfies Property A. The optimal intervention policy $\mathcal{B}^{*}$ is equal to $\mathcal{B}_{y^{*}}$, where $\boldsymbol{y}^{*}$ is the optimal intervention in the deterministic problem with $\overline{\boldsymbol{b}}=\mathbb{E}[\hat{\boldsymbol{b}}]$ taken as the status quo vector of standalone marginal returns.

### 5.2. Intervention on Variances

We next consider the case where the planner faces a vector of means, fixed at $\overline{\boldsymbol{b}}$, and, subject to that, can choose any random variable $\mathcal{B}$. It can be seen from (9) that, in this class of mean-neutral interventions, the expected welfare of an intervention $\mathcal{B}$ depends

[^15]only on the variance-covariance matrix of $\mathcal{B}$. Thus, the planner effectively faces the problem of intervening on variances, which we analyze for all cost functions satisfying certain symmetries.

Assumption 5: The cost function satisfies two properties: (a) $K(\mathcal{B})=\infty$ if $\mathbb{E}[\boldsymbol{b}] \neq \overline{\boldsymbol{b}}$; (b) $K(\mathcal{B})=K(\tilde{\mathcal{B}})$ if $\tilde{\boldsymbol{b}}-\overline{\boldsymbol{b}}=\boldsymbol{O}(\boldsymbol{b}-\overline{\boldsymbol{b}})$, where $\boldsymbol{O}$ is an orthogonal matrix. (Analogously to our other notation, we use $\tilde{\boldsymbol{b}}$ for realizations of $\tilde{\mathcal{B}}$.)

Part (a) is a restriction on feasible interventions, namely, a restriction to interventions that are mean-neutral. Part (b) means that rotations of coordinates around the mean do not affect the cost of implementing a given distribution. This assumption gives the cost a directional neutrality, which ensures that our results are driven by the benefits side rather than by asymmetries operating through the costs. For an example where the assumption is satisfied, let $\boldsymbol{\Sigma}_{\mathcal{B}}$ be the variance-covariance matrix of the random variable $\mathcal{B}$. In particular, $\sigma_{i i}^{\mathcal{B}}$ is the variance of $b_{i}$. Suppose that the cost of implementing $\mathcal{B}$ with $\mathbb{E}[\boldsymbol{b}]=\overline{\boldsymbol{b}}$ is a function of the sum of the variances of the $b_{i}$ :

$$
K(\mathcal{B})= \begin{cases}\phi\left(\sum_{\in \mathcal{N}} \sigma_{i i}^{\mathcal{B}}\right) & \text { if } \mathbb{E}[\boldsymbol{b}]=\overline{\boldsymbol{b}}, \\ \infty & \text { otherwise } .\end{cases}
$$

The cost function (10) satisfies part (a) of Assumption 5. Moreover, it satisfies part (b) of Assumption 5 because $\sum_{i \in \mathcal{N}} \sigma_{i i}^{\mathcal{B}}=$ trace $\boldsymbol{\Sigma}_{\mathcal{B}}$; this trace is the sum of the eigenvalues of $\boldsymbol{\Sigma}_{\mathcal{B}}$, which is invariant to the transformation defined in part (b). ${ }^{31}$

Proposition 4-Variance Control: Consider problem (IT-G) with a cost of intervention satisfying Assumption 5. Suppose Assumptions 1 and 2 hold and the network game satisfies Property A. Let the optimal intervention be $\mathcal{B}^{*}$, and let $\boldsymbol{b}^{*}$ be a typical realization. We have the following:

1. Suppose the planner likes variance (i.e., in (9), $w>0$ ). If the game has strategic complements ( $\beta>0$ ), then $\operatorname{Var}\left(\boldsymbol{u}^{\ell}(\boldsymbol{G}) \cdot \boldsymbol{b}^{*}\right)$ is weakly decreasing in $\ell$; if the game has strategic substitutes $(\beta<0)$, then $\operatorname{Var}\left(\boldsymbol{u}^{\ell}(\boldsymbol{G}) \cdot \boldsymbol{b}^{*}\right)$ is weakly increasing in $\ell$.
2. Suppose the planner dislikes variance (i.e., $w<0$ ). If the game has strategic complements ( $\beta>0$ ), then $\operatorname{Var}\left(\boldsymbol{u}^{\ell}(\boldsymbol{G}) \cdot \boldsymbol{b}^{*}\right)$ is weakly increasing in $\ell$; if the game has strategic substitutes ( $\beta<0$ ), then $\operatorname{Var}\left(\boldsymbol{u}^{\ell}(\boldsymbol{G}) \cdot \boldsymbol{b}^{*}\right)$ is weakly decreasing in $\ell$.

We now provide the intuition for Proposition 4. Shocks to individual's standalone marginal returns create variability in the players' equilibrium actions. The assumption that the intervention is mean-neutral (part (a) of Assumption 5) leaves the planner to control only the variances and covariances of these marginal returns with her intervention. Hence, the solution to the intervention problem describes what the planner should do to induce second moments of the action distribution that maximize ex ante expected welfare.

Suppose first that investments are strategic complements. Then a perfectly correlated (random) shock in individual standalone marginal returns is amplified by strategic interactions. In fact, the type of shock that is most amplifying (at a given size) is the one that

[^16]is perfectly correlated across individuals: a common deviation from the mean is scaled by the vector $\boldsymbol{u}^{1}$-the individuals' eigenvector centralities. Such shocks are exactly what $\underline{b}_{1}^{*}=\boldsymbol{u}^{1}(\boldsymbol{G}) \cdot \boldsymbol{b}^{*}$ captures. Hence, this is the dimension of volatility that the planner most wants to increase if she likes variance in actions $(w>0)$ and most wants to decrease if she dislikes variance in actions ( $w<0$ ).

If investments are strategic substitutes, then a perfectly correlated shock does not create a lot of variance in actions: the first-order response of all individuals to an increase in their standalone marginal returns is to increase investment, but that in turn makes all individuals decrease their investment somewhat because of the strategic substitutability with their neighbors. Hence, highly positively correlated shocks do not translate into high volatility. The shock profiles (of a fixed norm) that create the most variability in equilibrium actions are actually the ones in which neighbors have negatively correlated shocks. A planner that likes variance in actions will then prioritize such shocks. Because the last eigenvector of the system has entries that are as different as possible across neighbors, this is exactly the type of volatility that will be most amplified, and this is what the planner will focus on most.

Example 3-Illustration in the Case of the Circle: Figure 1 depicts six of the eigenvectors/principal components of a circle network with 14 nodes. The first principal component is a positive vector and so $\mathcal{B}$ projected on $\boldsymbol{u}^{1}(\boldsymbol{G})$ captures shocks that are positively correlated across all players. The second principal component (top left panel of Figure 1) splits the graph into two sides, one with positive entries and the other with negative entries. Hence, $\mathcal{B}$ projected on $\boldsymbol{u}^{2}(\boldsymbol{G})$ captures shocks that are highly positively correlated on each side of the circle network, with the two opposite sides of the circle being anticorrelated. As we move along the sequence of eigenvectors $\boldsymbol{u}^{\ell}$, we can see that $\mathcal{B}$ projected on the $\ell$ th eigenvector represents patterns of shocks that "vary more" across the network. At the extreme, $\mathcal{B}$ projected on $\boldsymbol{u}^{14}(\boldsymbol{G})$ (bottom-right panel of Figure 1) captures the component of shocks that is perfectly anti-correlated across neighbors. ${ }^{32}$

## 6. CONCLUDING REMARKS

We have studied the problem of a planner who seeks to optimally target incentive changes in a network game. Our framework allows for a broad class of strategic and nonstrategic spillovers across neighbors. The main contribution of the paper is methodological: we show that principal components of the network of interaction provide a useful basis for analyzing the effects of an intervention. This decomposition leads to our main result: there is a close connection between the strategic properties of the game (whether actions are strategic complements or substitutes) and the weight that different principal components receive in the optimal intervention. To develop these ideas in the simplest way, we have focused on a model in which the matrix of interaction is symmetric, the costs of intervention are quadratic, and the intervention itself takes the form of altering the standalone marginal returns of actions. In the Supplemental Material, we relax these restrictions and develop extensions of our approach to non-symmetric matrices of interaction and to more general costs of intervention, including a model where interventions occur via monetary incentives for activity. We also relax Property A, a technical condition which facilitated our basic analysis, and cover a more general class of externalities.

[^17]We briefly mention two further applications. In some circumstances, the planner seeks a budget-balanced tax/subsidy scheme in order to improve the economic outcome. In an oligopoly market, for example, a planner could tax some suppliers, thereby increasing their marginal costs, and then use that tax revenue to subsidize other suppliers. The planner will solve a problem similar to the one we have studied here, with the important difference that she will face a different constraint-namely, a budget-balance constraint. In ongoing work, Galeotti, Golub, Goyal, Talamàs, and Tamuz (2020) show that the principal component approach that we employed in this paper is useful in deriving the optimal taxation scheme and, in turn, in determining the welfare gains that can be achieved via tax/subsidy interventions in supply chains. ${ }^{33}$

We have focused on interventions that alter the standalone marginal returns of individuals. Another interesting problem is the study of interventions that alter the matrix of interaction. We hope this paper stimulates further work along these lines.

## APPENDIX: PROOFS

Proof of Theorem 1: We wish to solve

$$
\begin{array}{rl}
\max _{\boldsymbol{b}} & w \boldsymbol{a}^{\top} \boldsymbol{a} \\
\text { s.t.: } & {[\boldsymbol{I}-\beta \boldsymbol{G}] \boldsymbol{a}=\boldsymbol{b},} \\
& \sum_{i \in \mathcal{N}}\left(b_{i}-\hat{b}_{i}\right)^{2} \leq C .
\end{array}
$$

We transform the maximization problem into the basis given by the principal components of $\boldsymbol{G}$. To this end, we first rewrite the cost and the objective in the principal components basis, using the fact that norms do not change under the orthogonal transformation $\boldsymbol{U}^{\top}$. (The norm symbol $\|\cdot\|$ always refers to the Euclidean norm.) Letting $\boldsymbol{y}=\boldsymbol{b}-\hat{\boldsymbol{b}}$,

$$
K(\boldsymbol{b}, \hat{\boldsymbol{b}})=\sum_{i \in \mathcal{N}} y_{i}^{2}=\|\boldsymbol{y}\|_{2}^{2}=\sum_{\ell=1}^{n} \underline{y}_{\ell}^{2}
$$

and

$$
w \boldsymbol{a}^{\top} \boldsymbol{a}=w\|\boldsymbol{a}\|^{2}=w\|\underline{\boldsymbol{a}}\|^{2}=w \underline{\boldsymbol{a}^{\top}} \underline{\boldsymbol{a}} .
$$

By recalling that, in equilibrium, $\underline{\boldsymbol{a}}^{*}=[\boldsymbol{I}-\boldsymbol{\beta} \boldsymbol{\Lambda}]^{-1} \underline{\boldsymbol{b}}$, and using the definition $\alpha_{\ell}= \frac{1}{\left(1-\beta \lambda_{\ell}(\boldsymbol{G})\right)^{2}}$, the intervention problem (IT) can be rewritten as

$$
\begin{aligned}
\max _{\underline{\boldsymbol{b}}} w & \sum_{\ell=1}^{n} \alpha_{\ell} \underline{b}_{\ell}^{2} \\
\text { s.t. } & \sum_{\ell=1}^{n} \underline{y}_{\ell}^{2} \leq C .
\end{aligned}
$$

(IT-PC)

[^18]We now transform the problem so that the control variable is $\boldsymbol{x}$ where $x_{\ell}=y_{\ell} / \underline{\hat{b}}_{\ell}$. We obtain

$$
\begin{array}{rl}
\max _{x} & w \sum \ell=1^{n} \alpha_{\ell}\left(1+x_{\ell}\right)^{2} \underline{\hat{b}}_{\ell}^{2} \\
\text { s.t. } \quad \sum_{\ell=1}^{n} \hat{\underline{b}}_{\ell}^{2} x_{\ell}^{2} \leq C .
\end{array}
$$

Note that, for all $\ell, \alpha_{\ell}$ are well-defined (by Assumption 1) and strictly positive (by genericity of $\boldsymbol{G}$ ). This has two implications. ${ }^{34}$

First, at the optimal solution $\boldsymbol{x}^{*}$, the resource constraint problem must bind. To see this, note that Assumption 3 says that either $w>0$, or $w<0$ and $\sum_{\ell=1}^{n} \hat{\underline{b}}_{\ell}^{2}>C$. Suppose that at the optimal solution, the constraint does not bind. Then, without violating the constraint, we can slightly increase or decrease any $x_{\ell}$. If $w>0$ (resp. $w<0$ ), the increase or the decrease is guaranteed to increase (resp. decrease) the corresponding $\left(x_{\ell}+1\right)^{2}$ (since the $\alpha_{\ell}$ are all strictly positive).

Second, we show that the optimal solution $\boldsymbol{x}^{*}$ satisfies $x_{\ell}^{*} \geq 0$ for every $\ell$ if $w>0$, and $x_{\ell}^{*} \in[-1,0]$ for every $\ell$ if $w<0$. Suppose $w>0$ and, for some $\ell, x_{\ell}^{*}<0$. Then $\left[-x_{\ell}^{*}+\right. 1]^{2}>\left[x_{\ell}^{*}+1\right]^{2}$. Since $w>0$ and every $\alpha_{\ell}$ is positive, we can raise the aggregate utility without changing the cost by flipping the sign of $x_{\ell}^{*}$. Analogously, suppose $w<0$. It is clear that if $x_{\ell}^{*}<-1$, then by setting $x_{\ell}=-1$, the objective improves and the constraint is relaxed; hence, at the optimum, $x_{\ell}^{*} \geq-1$. Suppose next that $x_{\ell}>0$ for some $\ell$. Then $\left[-x_{\ell}^{*}+1\right]^{2}<\left[x_{\ell}^{*}+1\right]^{2}$. Since $w<0$ and every $\alpha_{\ell}$ is positive, we can improve the value of the objective function without changing the cost by flipping the sign of $x_{\ell}^{*}$.

We now complete the proof. Observe that the Lagrangian corresponding to the maximization problem is

$$
\mathcal{L}=w \sum_{\ell=1}^{n} \alpha_{\ell}\left(1+x_{\ell}\right)^{2} \underline{\hat{b}}_{\ell}+\mu\left[C-\sum_{\ell=1}^{n} \hat{b}_{\ell}^{2} x_{\ell}^{2}\right] .
$$

Taking our observation above that the constraint is binding at $\boldsymbol{x}=\boldsymbol{x}^{*}$, together with the standard results on the Karush-Kuhn-Tucker conditions, the first-order conditions must hold exactly at the optimum with a positive $\mu$ :

$$
0=\frac{\partial \mathcal{L}}{\partial x_{\ell}}=2 \hat{b}_{\ell}^{2}\left[w \alpha_{\ell}\left(1+x_{\ell}^{*}\right)-\mu x_{\ell}^{*}\right]=0 .
$$

We take a generic $\hat{\boldsymbol{b}}$ such that $\hat{\underline{b}}_{\ell} \neq 0$ for all $\ell$. If, for some $\ell$, we had $\mu=w \alpha_{\ell}$, then the right-hand side of the second equality in (11) would be $2 \hat{b}_{\ell}^{2} w \alpha_{\ell}$, which, by the generic assumption we just made and the positivity of $\alpha_{\ell}$, would contradict (11). Thus, the following holds with a nonzero denominator:

$$
x_{\ell}^{*}=\frac{w \alpha_{\ell}}{\mu-w \alpha_{\ell}}
$$

[^19]and the Lagrange multiplier $\mu$ is therefore pinned down by

$$
\sum_{\ell=1}^{n} w^{2} \hat{b}_{\ell}^{2}\left(\frac{\alpha_{\ell}}{\mu-w \alpha_{\ell}}\right)^{2}=C .
$$

Note finally that

$$
\begin{aligned}
\rho\left(\boldsymbol{y}^{*}, \boldsymbol{u}^{\ell}(\boldsymbol{G})\right) & =\frac{\boldsymbol{y}^{*} \cdot \boldsymbol{u}^{\ell}(\boldsymbol{G})}{\left\|\boldsymbol{y}^{*}\right\|\left\|\boldsymbol{u}^{\ell}(\boldsymbol{G})\right\|} \\
& =\frac{\underline{y}_{\ell}^{*}}{\sqrt{C}}=\frac{\hat{b}_{\ell} x_{\ell}^{*}}{\sqrt{C}}=\frac{\|\hat{\boldsymbol{b}}\|}{\sqrt{C}} \rho\left(\hat{\boldsymbol{b}}, \boldsymbol{u}^{\ell}(\boldsymbol{G})\right) x_{\ell}^{*} \propto_{\ell} \rho\left(\hat{\boldsymbol{b}}, \boldsymbol{u}^{\ell}(\boldsymbol{G})\right) x_{\ell}^{*}
\end{aligned}
$$

Proof of Proposition 1: Part 1. From expression (6) of Theorem 1, it follows that if $C \rightarrow 0$, then $\mu \rightarrow \infty$. The result follows by noticing that

$$
\frac{r_{\ell}^{*}}{r_{\ell^{\prime}}^{*}}=\frac{\alpha_{\ell}}{\alpha_{\ell^{\prime}}} \frac{\mu-w \alpha_{\ell}^{\prime}}{\mu-w \alpha_{\ell}}
$$

Part 2. Suppose that $\beta>0$. Using the derivation of the last part of the proof of Theorem 1, we write

$$
\rho\left(\boldsymbol{y}^{*}, \boldsymbol{u}^{\ell}(\boldsymbol{G})\right)=\frac{\|\hat{\boldsymbol{b}}\|}{\sqrt{C}} \rho\left(\hat{\boldsymbol{b}}, \boldsymbol{u}^{\ell}(\boldsymbol{G})\right) x_{\ell}^{*}
$$

with $x_{\ell}^{*}=\frac{w \alpha_{\ell}}{\mu-w \alpha_{\ell}}$. From expression (6) of Theorem 1, it follows that if $C \rightarrow \infty$, then $\mu \rightarrow w \alpha_{1}$. This implies that $x_{\ell}^{*} \rightarrow \frac{\alpha_{\ell}}{\alpha_{1}-\alpha_{\ell}}$ for all $\ell \neq 1$. As a result, if $C \rightarrow \infty$, then $\rho\left(\boldsymbol{y}^{*}, \boldsymbol{u}^{\ell}(\boldsymbol{G})\right) \rightarrow$ 0 for all $\ell \neq 1$. Furthermore, we can rewrite expression (6) of Theorem 1 as

$$
\sum_{\ell=1}^{n}\left(\|\hat{\boldsymbol{b}}\| \rho\left(\hat{\boldsymbol{b}}, \boldsymbol{u}^{\ell}(\boldsymbol{G})\right) \frac{x_{\ell}^{*}}{\sqrt{C}}\right)^{2}=1
$$

and therefore

$$
\lim _{C \rightarrow \infty} \sum_{\ell=1}^{n}\left(\|\hat{\boldsymbol{b}}\| \rho\left(\hat{\boldsymbol{b}}, \boldsymbol{u}^{\ell}(\boldsymbol{G})\right) \frac{x_{\ell}^{*}}{\sqrt{C}}\right)^{2}=\lim _{C \rightarrow \infty}\left(\|\hat{\boldsymbol{b}}\| \rho\left(\hat{\boldsymbol{b}}, \boldsymbol{u}^{1}(\boldsymbol{G})\right) \frac{x_{1}^{*}}{\sqrt{C}}\right)^{2}=1,
$$

where the first equality follows because $x_{\ell}^{*} \rightarrow \frac{\alpha_{\ell}}{\alpha_{1}-\alpha_{\ell}}$ for all $\ell \neq 1$. The proof for the case of $\beta<0$ follows the same steps, with the only exception that if $C \rightarrow \infty$, then $\mu \rightarrow w \alpha_{n}$. Q.E.D.

Proof of Proposition 2: We first prove the result on welfare and then turn to the result on cosine similarity.

Welfare. Consider the case of strategic complementarities, $\beta>0$. Define by $\tilde{x}$ the simple intervention, and note that $\tilde{x}_{1}=\sqrt{C} / \underline{\hat{b}}_{1}$ and that $\tilde{x}_{\ell}=0$ for all $\ell>1$. The aggregate utility obtained under the simple intervention is

$$
W^{s}=\sum_{\ell=1}^{n} \hat{\underline{b}}_{\ell}^{2} \alpha_{\ell}\left(1+\tilde{x}_{\ell}\right)^{2}=\hat{\underline{b}}_{1}^{2} \alpha_{1} \tilde{x}_{1}\left(\tilde{x}_{1}+2\right)+\sum_{\ell=1}^{n} \alpha_{\ell} \hat{\underline{b}}_{\ell}^{2} .
$$

The aggregate utility at the optimal intervention is

$$
W^{*}=\sum_{\ell=1}^{n} \hat{b}_{\ell}^{2} \alpha_{\ell}\left(1+x_{\ell}^{*}\right)^{2}=\hat{b}_{1}^{2} \alpha_{1} x_{1}^{*}\left(x_{1}^{*}+2\right)+\sum_{\ell=2}^{n} \hat{b}_{\ell}^{2} \alpha_{\ell} x_{\ell}^{*}\left(x_{\ell}^{*}+2\right)+\sum_{\ell=1}^{n} \alpha_{\ell} \hat{b}_{\ell}^{2}
$$

Hence, letting $D=\underline{\hat{b}}_{1}^{2} \alpha_{1} \tilde{x}_{1}\left(\tilde{x}_{1}+2\right)+\sum_{\ell=1}^{n} \alpha_{\ell} \hat{\hat{b}}_{\ell}^{2}$,

$$
\begin{array}{rlr}
\frac{W^{*}}{W^{s}} & =\frac{\hat{b}_{1}^{2} \alpha_{1} x_{1}^{*}\left(x_{1}^{*}+2\right)+\sum_{\ell=1}^{n} \alpha_{\ell} \hat{b}_{\ell}^{2}}{D}+\frac{\sum_{\ell=2}^{n} \hat{b}_{\ell}^{2} \alpha_{\ell} x_{\ell}^{*}\left(x_{\ell}^{*}+2\right)}{D} & \\
& \leq 1+\frac{\sum_{\ell=2}^{n} \hat{b}_{\ell}^{2} \alpha_{\ell} x_{\ell}^{*}\left(x_{\ell}^{*}+2\right)}{D} & \\
& \leq 1+\frac{\sum_{\ell=2}^{n} \hat{b}_{\ell}^{2} \alpha_{\ell} x_{\ell}^{*}\left(x_{\ell}^{*}+2\right)}{\hat{b}_{1}^{2} \alpha_{1} \tilde{x}_{1}^{2}} & \\
& =1+\frac{\sum_{\ell=2}^{n} \hat{b}_{\ell}^{2} \alpha_{\ell} x_{\ell}^{*}\left(x_{\ell}^{*}+2\right)}{\alpha_{1} C} & \\
& \leq 1+\frac{2 \alpha_{1}-\alpha_{2}^{*}}{\alpha_{1}} \frac{\|\hat{\boldsymbol{b}}\|^{2}}{C}\left(\frac{\alpha_{2}}{\alpha_{1}-\alpha_{2}}\right)^{2} & \\
& \leq 1+\frac{2\|\hat{\boldsymbol{b}}\|^{2}}{C}\left(\frac{\alpha_{2}}{\alpha_{1}-\alpha_{2}}\right)^{2} & \\
& \text { see calculation below } D \text { are positive }
\end{array}
$$

The fact $\underline{b}_{1}^{2} \tilde{x}_{1}^{2}=C$, used above, follows because the simple policy allocates the entire budget to changing $\underline{b}_{1}$. The inequality after that statement follows because

$$
\begin{array}{rlr}
\sum_{\ell=2}^{n} \hat{b}_{\ell}^{2} \alpha_{\ell} x_{\ell}^{*}\left(x_{\ell}^{*}+2\right) & \leq \alpha_{2} \sum_{\ell=2}^{n} \hat{b}_{\ell}^{2} x_{\ell}^{*}\left(x_{\ell}^{*}+2\right) & \text { ordering of the } \alpha_{\ell} \\
& \leq \alpha_{2} x_{2}^{*}\left(x_{2}^{*}+2\right) \sum_{\ell=2}^{n} \hat{b}_{\ell}^{2} & \text { Corollary } 1 \\
& \leq \alpha_{2} \frac{w \alpha_{2}}{\mu-w \alpha_{2}}\left(\frac{w \alpha_{2}}{\mu-w \alpha_{2}}+2\right) \sum_{\ell=2}^{n} \underline{\hat{b}}_{\ell}^{2} & \text { Theorem 1 } \\
& \leq \alpha_{2} \frac{w \alpha_{2}}{w \alpha_{1}-w \alpha_{2}}\left(\frac{w \alpha_{2}}{w \alpha_{1}-w \alpha_{2}}+2\right)\|\underline{\hat{b}}\|^{2} & \\
& =\left(\frac{\alpha_{2}}{\alpha_{1}-\alpha_{2}}\right)^{2}\left(2 \alpha_{1}-\alpha_{2}\right)\|\hat{\boldsymbol{b}}\|^{2} . &
\end{array}
$$

Hence, the inequality

$$
C>\frac{2\|\hat{\boldsymbol{b}}\|^{2}}{\epsilon}\left(\frac{\alpha_{2}}{\alpha_{1}-\alpha_{2}}\right)^{2}
$$

is sufficient to establish that $\frac{W^{*}}{W^{s}}<1+\epsilon$. The proof for the case of strategic substitutes follows the same steps; the only difference is that we use $\alpha_{n}$ instead of $\alpha_{1}$ and $\alpha_{n-1}$ instead of $\alpha_{2}$.

Cosine similarity. We now turn to the cosine similarity result. We focus on the case of strategic complements. The proof for the case of strategic substitutes is analogous. We start by writing a useful explicit expression for $\rho\left(\Delta \boldsymbol{b}^{*}, \sqrt{C} \boldsymbol{u}^{1}\right)$ :

$$
\rho\left(\Delta \boldsymbol{b}^{*}, \sqrt{C} \boldsymbol{u}^{1}\right)=\frac{\left(\boldsymbol{b}^{*}-\hat{\boldsymbol{b}}\right) \cdot\left(\sqrt{C} \boldsymbol{u}^{1}\right)}{\left\|\boldsymbol{b}^{*}-\hat{\boldsymbol{b}}\right\|\left\|\sqrt{C} \boldsymbol{u}^{1}\right\|}=\frac{\left(\boldsymbol{b}^{*}-\hat{\boldsymbol{b}}\right) \cdot\left(\boldsymbol{u}^{1}\right)}{\sqrt{C}},
$$

where the last equality follows because, at the optimum, $\left\|\boldsymbol{b}^{*}-\hat{\boldsymbol{b}}\right\|^{2}=C$. At the optimal intervention, by Theorem 1,

$$
\underline{b}_{\ell}^{*}-\underline{\hat{b}}_{\ell}=\frac{w \alpha_{\ell}}{\mu-w \alpha_{\ell}} \underline{\hat{b}}_{\ell} ;
$$

now, using the definition $\underline{\boldsymbol{b}}=\boldsymbol{U}^{T} \boldsymbol{b}$, we have that

$$
b_{i}^{*}-\hat{b}_{i}=w \sum_{\ell=1}^{n} u_{\ell}^{i} \frac{\alpha_{\ell}}{\mu-w \alpha_{\ell}} \hat{b}_{\ell}
$$

and therefore

$$
\left(\boldsymbol{b}^{*}-\hat{\boldsymbol{b}}\right) \cdot \boldsymbol{u}^{1}=\sum_{i} \sum_{\ell=1}^{n} u_{i}^{1} u_{i}^{\ell} \frac{w \alpha_{\ell}}{\mu-w \alpha_{\ell}} \hat{\underline{b}}_{\ell}=\sum_{\ell=1}^{n} \frac{w \alpha_{\ell}}{\mu-w \alpha_{\ell}} \hat{\underline{b}}_{\ell}\left(\boldsymbol{u}^{1} \cdot \boldsymbol{u}^{\ell}\right)=\frac{w \alpha_{1}}{\mu-w \alpha_{1}} \hat{\underline{b}}_{1} .
$$

Hence, using this in equation (12), we can deduce that

$$
\rho\left(\Delta \boldsymbol{b}^{*}, \boldsymbol{u}^{1}\right)=\frac{1}{\sqrt{C}} \frac{w \alpha_{1}}{\mu-w \alpha_{1}} \hat{b}_{1} \geq \sqrt{1-\epsilon} \quad \text { iff } \quad\left(\frac{w \alpha_{1}}{\mu-w \alpha_{1}}\right)^{2} \hat{b}_{1}^{2}-C(1-\epsilon) \geq 0 .
$$

We now claim that the inequality in the above display after the "if and only if" follows from our hypothesis that

$$
C>\frac{2\|\hat{\boldsymbol{b}}\|^{2}}{\epsilon}\left(\frac{\alpha_{2}}{\alpha_{1}-\alpha_{2}}\right)^{2} .
$$

This claim is established by the following lemma.
Lemma 1: Assume

$$
C>\frac{2\|\hat{\boldsymbol{b}}\|^{2}}{\epsilon}\left(\frac{\alpha_{2}}{\alpha_{1}-\alpha_{2}}\right)^{2} .
$$

Then

$$
\left(\frac{w \alpha_{1}}{\mu-w \alpha_{1}}\right)^{2} \hat{b}_{1}^{2} \geq C(1-\epsilon) .
$$

Proof of Lemma 1: Note that

$$
C>\frac{2\|\hat{\boldsymbol{b}}\|^{2}}{\epsilon}\left(\frac{\alpha_{2}}{\alpha_{1}-\alpha_{2}}\right)^{2} \Longrightarrow \epsilon C>\|\hat{\boldsymbol{b}}\|^{2}\left(\frac{\alpha_{2}}{\alpha_{1}-\alpha_{2}}\right)^{2}
$$

and therefore

$$
C(1-\epsilon)<C-\|\hat{\boldsymbol{b}}\|^{2}\left(\frac{\alpha_{2}}{\alpha_{1}-\alpha_{2}}\right)^{2} .
$$

But then we have the following chain of statements, explained immediately after the display:

$$
\begin{aligned}
\left(\frac{w \alpha_{1}}{\mu-w \alpha_{1}}\right)^{2} \hat{b}_{1}^{2}-C(1-\epsilon) & \geq\left(\frac{w \alpha_{1}}{\mu-w \alpha_{1}}\right)^{2} \hat{b}_{1}^{2}-C+\|\hat{\boldsymbol{b}}\|^{2}\left(\frac{\alpha_{2}}{\alpha_{1}-\alpha_{2}}\right)^{2} \\
& =\left(\frac{w \alpha_{1}}{\mu-w \alpha_{1}}\right)^{2} \hat{b}_{1}^{2}-\sum_{\ell=1}^{n}\left(\frac{w \alpha_{\ell}}{\mu-w \alpha_{\ell}}\right)^{2} \hat{b}_{\ell}^{2}+\|\hat{\boldsymbol{b}}\|^{2}\left(\frac{\alpha_{2}}{\alpha_{1}-\alpha_{2}}\right)^{2} \\
& =\|\hat{\boldsymbol{b}}\|^{2}\left(\frac{\alpha_{2}}{\alpha_{1}-\alpha_{2}}\right)^{2}-\sum_{\ell=2}^{n}\left(\frac{w \alpha_{\ell}}{\mu-w \alpha_{\ell}}\right)^{2} \hat{b}_{\ell}^{2} \\
& =\left(\frac{\alpha_{2}}{\alpha_{1}-\alpha_{2}}\right)^{2} \sum_{\ell=1}^{n} \hat{b}_{\ell}^{2}-\sum_{\ell=2}^{n}\left(\frac{w \alpha_{\ell}}{\mu-w \alpha_{\ell}}\right)^{2} \hat{b}_{\ell}^{2}>0 .
\end{aligned}
$$

The first inequality follows from substituting the upper bound on $C(1-\epsilon)$, statement (15) above, which we derived from our initial condition on $C$. The equality after that follows by substituting the condition on the binding budget constraint at the optimum, which we derived in Theorem 1. The next equality follows by isolating the term for the first component in the summation and by noticing that that cancels with the first term. The next equality follows by noticing that $\|\hat{\boldsymbol{b}}\|^{2}=\|\underline{\hat{\boldsymbol{b}}}\|^{2}$. The final inequality follows because, from the facts that $\mu>w \alpha_{1}$ and that $\alpha_{1}>\alpha_{2}>\cdots>\alpha_{n}$, we can deduce that for each $\ell>1$,

$$
\frac{w \alpha_{\ell}}{\mu-w \alpha_{\ell}}<\frac{w \alpha_{\ell}}{w \alpha_{1}-w \alpha_{\ell}}=\frac{\alpha_{\ell}}{\alpha_{1}-\alpha_{\ell}}<\frac{\alpha_{2}}{\alpha_{1}-\alpha_{2}} .
$$

This concludes the proof of Proposition 2.

## REFERENCES

Akbarpour, M., S. Malladi, and A. Saberi (2020): "Just a Few Seeds More: Value of Network Information for Diffusion" Report, Graduate School of Business, Stanford University. [2447]
Allouch, N. (2015): "On the Private Provision of Public Goods on Networks," Journal of Economic Theory, 157, 527-552. [2450]

- (2017): "Aggregation in Networks," Discussion Paper 1718, School of Economics, University of Kent.

Alon, N., And N. Kahale (1997): "A Spectral Technique for Coloring Random 3-Colorable Graphs," SIAM Journal on Computing, 26, 1733-1748. [2457]
Angeletos, G.-M., and A. Pavan (2007): "Efficient Use of Information and Social Value of Information," Econometrica, 75, 1103-1142. [2446,2451]
Ballester, C., A. Calvó-Armengol, and Y. Zenou (2006): "Who's Who in Networks. Wanted: The Key Player," Econometrica, 74, 1403-1417. [2446,2447,2449,2450]
Banerjee, A., A. G. Chandrasekhar, E. Duflo, and M. O. Duflo (2013): "The Diffusion of Microfinance," Science, 341, 1236498. [2447]
Belhaj, M., F. Deroїan, and S. Safi (2020): "Targeting in Networks under Costly Agreements," Report, Aix-Marseille University. [2447]
Bloch, F., and N. Querou (2013): "Pricing in Social Networks," Games and Economic Behavior, 80, 263-281. [2447]
Borgatti, S. (2006): "Identifying Sets of Key Players in a Social Network," Computational and Mathematical Organization Theory, 12, 21-34. [2447]
Bramoullé, Y., and R. Kranton (2007): "Public Goods in Networks," Journal of Economic Theory, 135, 478-494. [2446,2450]
Bramoullé, Y., R. Kranton, and M. d'Amours (2014): "Strategic Interaction and Networks," The American Economic Review, 104, 898-930. [2447,2449]
Candogan, O., K. Bimpikis, and A. Ozdaglar (2012): "Optimal Pricing in Networks With Externalities," Operations Research, 60, 883-905. [2447]
Chung, F. R., and F. C. Graham (1997): Spectral Graph Theory, Vol. 92. American Mathematical Soc. [2452]
Cvetkovic, D., D. M. Cvetković, P. Rowlinson, and S. Simic (1997): Eigenspaces of Graphs, Vol. 66. Cambridge University Press. [2452]
Davies, E. B., G. M. Gladwell, J. Leydold, and P. F. Stadler (2001): "Discrete Nodal Domain Theorems," Linear Algebra and its Applications, 336, 51-60. [2452]
Demange, G. (2017): "Optimal Targeting Strategies in a Network Under Complementarities," Games and Economic Behaviour, 105, 84-103. [2447]
Desai, M., And V. Rao (1994): "A Characterization of the Smallest Eigenvalue of a Graph," Journal of Graph Theory, 18, 181-194. [2457]
Fainmesser, I., and A. Galeotti (2017): "Pricing Network Effects," Review of Economic Studies, 83, 165198. [2447]

Gaitonde, J., J. Kleinberg, and É. Tardos (2020): "Adversarial Perturbations of Opinion Dynamics in Networks," Report, Cornell University, https://arxiv.org/abs/2003.07010. [2464]
Galeotti, A., and S. Goyal (2009): "Influencing the Influencers: A Theory of Strategic Diffusion," The Rand Journal of Economics, 40, 509-532. [2447]

- (2010): "The Law of the Few," American Economic Review, 100, 1468-1492. [2450]

Galeotti, A., and B. W. Rogers (2013): "Strategic Immunization and Group Structure," American Economic Journal: Microeconomics, 5, 1-32. [2447]
Galeotti, A., B. Golub, S. Goyal, E. Talamàs, and O. Tamuz (2020): "Targeted Taxes and Subsidies in Supply Chains," Report. [2464]
Galeotti, A., B. Golub S. Goyal (2020): "Supplement to 'Targeting Interventions in Networks'," Econometrica Supplemental Material, 88, https://doi.org/10.3982/ECTA16173. [2448]
Galeotti, A., S. Goyal, M. O. Jackson, F. Vega-Redondo, and L. Yariv (2010): "Network Games," Review of Economic Studies, 77, 218-244. [2447]
Golub, B., and M. O. Jackson (2012): "How Homophily Affects the Speed of Learning and Best-Response Dynamics," The Quarterly Journal of Economics, 127, 1287-1338. [2459]
Golub, B., and S. Morris (2020): "Expectations, Networks and Conventions," Report, Department of Eonomics, Harvard University, https://arxiv.org/abs/2009.13802. [2460]
Goyal, S., and J. Moraga-Gonzalez (2001): "R\&D Networks," The Rand Journal of Economics, 32, 686707. [2446,2450]

Goyal, S., J. Moraga, and M. van der Leis (2006): "Economics: An Emerging Small World?" Journal of Political Economy, 114, 403-412. [2447]
Hartfiel, D., and C. D. Meyer (1998): "On the Structure of Stochastic Matrices With a Subdominant Eigenvalue Near 1," Linear Algebra and its Applications, 272, 193-203. [2459]
Jackson, M., B. W. Rogers, and Y. Zenou (2017): "The Economic Consequences of Social-Network Structure," Journal of Economic Literature, 55, 49-95. [2446]
Kempe, D., J. Kleinberg, and E. Tardos (2003): "Maximizing the Spread of Influence Through a Social Network," in Proceedings 9th ACM SIGKDD International Conference on Knowledge Discovery and Data Mining. [2447]

Lambert, N. S., G. Martini, and M. Ostrovsky (2018): "Quadratic Games," Working Paper No. 24914, NBER. [2460]
Leduc, M. V., M. O. Jackson, and R. Johari (2017): "Pricing and Referrals in Diffusion on Networks," Games and Economic Behavior, 104, 568-594. [2447]
Levin, D. A., Y. Peres, and E. L. Wilmer (2009): Markov Chains and Mixing Times. Providence, RI: American Mathematical Society. [2459]
Morris, S., and H. S. Shin (2002): "Social Value of Public Information," American Economic Review, 92, 1521-1534. [2446,2451]
Rogers, E. (1983): Diffusion of Innovations (Third Ed.). New York: Free Press. [2447]
Spielman, D. A. (2007): "Spectral Graph Theory and Its Applications," in 48th Annual IEEE Symposium on Foundations of Computer Science (FOCS'07). IEEE, 29-38. [2452]
Urschel, J. C. (2018): "Nodal Decompositions of Graphs," Linear Algebra and its Applications, 539, 60-71. [2452]
Valente, T. (2012): "Network Interventions," Science, 337, 49-53. [2447]

Co-editor Dirk Bergemann handled this manuscript.
Manuscript received 12 March, 2018; final version accepted 14 April, 2020; available online 23 April, 2020.

[^0]:
    Andrea Galeotti: agaleotti@london.edu
    Benjamin Golub: bgolub@fas.harvard.edu
    Sanjeev Goyal: sg472@cam.ac.uk
    We are grateful to five anonymous referees for helpful comments. We have also benefited from conversations with Francis Bloch, Drew Fudenberg, Eric Maskin, Matthew Jackson, Asuman Ozdaglar, Francesca Parise, Omer Tamuz, Eduard Talamàs, John Urschel, Xavier Vives, Rakesh Vohra, Alex Wolitzky, and Leeat Yariv. Ria Granzier-Nakajima, Joerg Kalbfuss, Gustavo Paez, Rithvik Rao, Brit Sharoni, and Eduard Talamàs provided exceptional research assistance. We thank Sihua Ding, Fakhteh Saadatniaki, Alan Walsh, and Yves Zenou for detailed comments on earlier drafts. Andrea Galeotti gratefully acknowledges financial support from the European Research Council through the ERC-consolidator grant (award no. 724356) and the European University Institute through the Internal Research Grant. Benjamin Golub gratefully acknowledges financial support from The Pershing Square Fund for Research on the Foundations of Human Behavior and the National Science Foundation (SES-1658940, SES-1629446). Goyal gratefully acknowledges support from the Wesley Clair Mitchell Visiting Professorship at Columbia University during Spring 2020.

[^1]:
    ${ }^{1}$ This framework encompasses a number of well-known economic examples from the literature: spillovers in educational/criminal effort (Ballester, Calvó-Armengol, and Zenou (2006)), research collaboration among firms (Goyal and Moraga-Gonzalez (2001)), local public goods (Bramoullé and Kranton (2007)), investment games and beauty contests (Angeletos and Pavan (2007), Morris and Shin (2002)), and peer effects in smoking (Jackson, Rogers, and Zenou (2017)).
    ${ }^{2}$ We use the standard notion of cosine similarity: the similarity of two vectors is the cosine of the angle between them in a plane they jointly define.

[^2]:
    ${ }^{3}$ In similarity terms, this means that the optimal intervention has a cosine similarity of nearly 1 to the first or last principal component (depending on the case), and a similarity of nearly 0 to all other principal components.
    ${ }^{4}$ See, for example, Goyal, Moraga, and van der Leij (2006), Ballester, Calvó-Armengol, and Zenou (2006), Bramoullé, Kranton, and d'Amours (2014), and Galeotti, Goyal, Jackson, Vega-Redondo, and Yariv (2010).
    ${ }^{5}$ For a general introduction to the subject, see Rogers (1983), Kempe, Kleinberg, and Tardos (2003), Borgatti (2006), and Valente (2012). Within economics, a prominent early contribution is Ballester, Calvó-Armengol, and Zenou (2006); recent contributions include Banerjee, Chandrasekhar, Duflo, and Duflo (2013), Belhaj, Deroïan and Safi (2020), Bloch and Querou (2013), Candogan, Bimpikis, and Ozdaglar (2012), Demange (2017), Fainmesser and Galeotti (2017), Galeotti and Goyal (2009), Galeotti and Rogers (2013), Leduc, Jackson, and Johari (2017), and Akbarpour, Malladi, and Saberi (2020).

[^3]:
    ${ }^{6}$ Appendix Section OA2.1 of the Supplemental Material (Galeotti, Golub, and Goyal (2020)) presents a discussion of the relationship between principal components and other network measures that have been studied in the literature.
    ${ }^{7}$ We extend our analysis to more general $\boldsymbol{G}$ in Supplemental Material Section OA3.2.

[^4]:
    ${ }^{8}$ An equivalent condition is for $|\beta|$ to be less than the reciprocal of the spectral radius of $\boldsymbol{G}$.
    ${ }^{9}$ See Ballester, Calvó-Armengol, and Zenou (2006) and Bramoullé, Kranton, and d'Amours (2014) for detailed discussions of this assumption and the interpretation of the solution given by (3).

[^5]: ${ }^{10}$ Other examples include workers keeping areas on a factory floor clean and safe, and businesses in a retail area contributing to the maintenance of their surroundings.

[^6]:
    ${ }^{11}$ See Spielman (2007), especially Section 16.5.1, on this interpretation. For book-length treatments of spectral graph theory, see Cvetkovic, Cvetković, Rowlinson, and Simic (1997) and Chung and Graham (1997).
    ${ }^{12}$ The circle network is invariant to rotations (cyclic permutations) of the nodes and so the eigenvectors here are determined only up to a rotation.
    ${ }^{13}$ For formal treatments of this phenomenon, see Davies, Gladwell, Leydold, and Stadler (2001) and Urschel (2018).

[^7]:
    ${ }^{14}$ Assumption 2 on the spectral radius implies that $\beta \boldsymbol{\Lambda}$ has no entries larger than 1 .
    ${ }^{15}$ In the local public goods application (recall Example 2), $w=-1$, and so when $C \geq\|\hat{\boldsymbol{b}}\|$, the optimal intervention satisfies $b_{i}^{*}=0$. Recalling our change of variables there ( $b_{i}=\left[\tau-\tilde{b}_{i}\right] / 2$ ), the optimal intervention in that case is to modify the endowment of each individual so that everyone accesses the optimal level of the local public good without investing.

[^8]: ${ }^{16}$ It can be verified that, for every $\ell \in\{1, \ldots, n-1\}$, the ratio $x_{\ell} / x_{\ell+1}$ is increasing (decreasing) in $\beta$ for the case of strategic complements (substitutes): thus the intensity of the strategic interaction shapes the relative importance of different principal components.

[^9]: ${ }^{17}$ Analogously, if $w<0$, for all $\ell, \ell^{\prime}$ such that $\alpha_{\ell}>\alpha_{\ell^{\prime}}$, we have that $\frac{w \alpha_{\ell}}{\mu-w \alpha_{\ell}}$ and $r_{\ell}^{*} / r_{\ell^{\prime}}^{*}$ are both decreasing in $C$.

[^10]:
    ${ }^{18}$ As costs are quadratic, a small relaxation in the budget around zero can have a large impact on aggregate welfare.
    ${ }^{19}$ When individuals' initial standalone marginal returns are zero ( $\hat{\boldsymbol{b}}=\mathbf{0}$ ), we can dispense with the approximations invoked for a large budget $C$. Assuming that $\boldsymbol{G}$ is generic, if $\hat{\boldsymbol{b}}=\mathbf{0}$, then, for any $C$, the entire budget is spent either (i) on changing $\underline{b}_{1}$ (if $\beta>0$ ) or (ii) on changing $\underline{b}_{n}$ (if $\beta<0$ ).
    ${ }^{20}$ About 125 times larger than $\|\widehat{\boldsymbol{b}}\|^{2}$.

[^11]:
    ${ }^{21}$ Supplemental Material Section OA2.1 presents a discussion of eigenvector centrality and how it compares to centrality measures that turn out to be important in related targeting problems.
    ${ }^{22}$ The last eigenvector of a graph is useful in diagnosing the bipartiteness of a graph and its chromatic number. Desai and Rao (1994) characterized the smallest eigenvalue of a graph and related it to a measure of the graph's bipartiteness. Alon and Kahale (1997) related the last eigenvector to a coloring of the underlying graph-a labeling of nodes by a minimal set of integers such that no neighboring nodes share the same label.
    ${ }^{23}$ The definition also specifies the interventions in more detail-that is, that they are proportional to the appropriate $u_{i}^{\ell}$. We could have instead left this flexible in this definition of simplicity and specified the dependence on the network explicitly in Proposition 2.

[^12]: ${ }^{24}$ Recall that $\left\|\frac{1}{n} \hat{\boldsymbol{b}}\right\|^{2}$ is equal to the sum of $\left(\frac{1}{n} \sum_{i \in \mathcal{N}} \hat{b}_{i}\right)^{2}$ (the squared mean of the entries of $\boldsymbol{b}$ ) and the sum of squared deviations of the entries of the vector $\hat{\boldsymbol{b}}$ from their mean.

[^13]:
    ${ }^{25}$ See Hartfiel and Meyer (1998), Levin, Peres, and Wilmer (2009), and Golub and Jackson (2012) for discussions and further citations to the literature on spectral gaps.
    ${ }^{26}$ The eigenvalue is in fact negative, as a consequence of the assumption that $g_{i i}=0$ for all $i$ : The trace of $\boldsymbol{G}$ is zero, and therefore its eigenvalues sum to 0 . By the Perron-Frobenius theorem, the maximum eigenvalue of the nonnegative matrix $\boldsymbol{G}$ is positive, so the minimum one must be negative.

[^14]:
    ${ }^{27}$ Intuitively, because $\boldsymbol{u}^{n}$ does not correspond to a perfect bipartition, it is easier for a vector orthogonal to $\boldsymbol{u}^{n}$ to achieve a similarly low value of $\sum_{i, j \in \mathcal{N}} g_{i j} u_{i} u_{j}$.
    ${ }^{28}$ The domain of this function is the set of all random vectors taking values in $\mathbb{R}^{n}$ defined on our probability space.
    ${ }^{29}$ It is possible to go further and allow for incomplete information among the individuals about each other's $b_{i}$. We do not pursue this substantial generalization here; see Golub and Morris (2020) and Lambert, Martini, and Ostrovsky (2018) for analyses in this direction.

[^15]: ${ }^{30}$ This reduction is justified as follows: since only the first two moments of standalone marginal returns affect equilibrium welfare, the planner should choose the cost-minimizing way to achieve a desired combination of these. We may take the cost of a given intervention to be the corresponding minimizer.

[^16]: ${ }^{31}$ When we look at the variance-covariance matrix of $\tilde{\boldsymbol{b}}$ defined by $\tilde{\boldsymbol{b}}-\overline{\boldsymbol{b}}=\boldsymbol{O}(\boldsymbol{b}-\overline{\boldsymbol{b}})$, the variance-covariance matrix becomes $\boldsymbol{O} \boldsymbol{\Sigma} \boldsymbol{O}^{\top}$, and this has the same eigenvalues and therefore the same trace.

[^17]: ${ }^{32}$ As usual in this example, a generic $\boldsymbol{G}$ will not be perfectly symmetric and so a particular orientation of these eigenvectors will be selected.

[^18]: ${ }^{33}$ In a recent paper, Gaitonde, Kleinberg and Tardos (2020) use spectral methods to study interventions that polarize opinions in a social network.

[^19]: ${ }^{34}$ Note that if Assumption 3 does not hold (i.e., $w<0$ and $\sum_{\ell=1}^{n} \hat{\underline{b}}_{\ell}^{2} \leq C$ ), then the optimal solution is $x_{\ell}^{*}=-1$ for all $\ell$. This is what we ruled out with Assumption 3, before Theorem 1.
