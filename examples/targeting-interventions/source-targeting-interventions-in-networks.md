# Targeting Interventions in Networks
ANDREA GALEOTTI
Department of Economics, London Business School
BENJAMIN GOLUB
Department of Economics, Harvard University
SANJEEV GOYAL
Faculty of Economics and Christ’s College, University of Cambridge
## Abstract
We study games in which a network mediates strategic spillovers and externalities
among the players. How does a planner optimally target interventions that change
individuals’ private returns to investment? We analyze this question by decomposing
any intervention into orthogonal principal components , which are determined by the
network and are ordered according to their associated eigenvalues. There is a close
connection between the nature of spillovers and the representation of various principal components in the optimal intervention. In games of strategic complements (substitutes), interventions place more weight on the top (bottom) principal components,
which reﬂect more global (local) network structure. For large budgets, optimal interventions are simple—they essentially involve only a single principal component.
**Keywords:** Targeting, interventions, networks, strategic interaction, externalities, peer effects, network games.
## 1. INTRODUCTION
WE study games among agents embedded in a network. The action of each agent—for example, a level of investment or effort—directly affects a subset of others, called neighbors
of that agent. This happens through two channels: spillover effects on others’ incentives,
as well as non-strategic externalities. A utilitarian planner with limited resources can intervene to change individuals’ incentives for taking the action. Our goal is to understand
how the planner can best target such interventions in view of the network and other primitives of the environment.
We now lay out the elements of the model in more detail. Individuals play a
simultaneous-move game with continuous actions. An agent’s action creates standalone
returns for that agent independent of anyone else’s action, but it also creates spillovers.
The intensity of these spillovers is described by a network, with the strength of a link
Andrea Galeotti: agaleotti@london.edu
Benjamin Golub: bgolub@fas.harvard.edu
Sanjeev Goyal: sg472@cam.ac.uk
We are grateful to ﬁve anonymous referees for helpful comments. We have also beneﬁted from conversations with Francis Bloch, Drew Fudenberg, Eric Maskin, Matthew Jackson, Asuman Ozdaglar, Francesca
Parise, Omer T amuz, Eduard T alamàs, John Urschel, Xavier Vives, Rakesh Vohra, Alex Wolitzky, and Leeat
Yariv. Ria Granzier-Nakajima, Joerg Kalbfuss, Gustavo Paez, Rithvik Rao, Brit Sharoni, and Eduard T alamàs
provided exceptional research assistance. We thank Sihua Ding, Fakhteh Saadatniaki, Alan Walsh, and Yves
Zenou for detailed comments on earlier drafts. Andrea Galeotti gratefully acknowledges ﬁnancial support
from the European Research Council through the ERC-consolidator grant (award no. 724356) and the European University Institute through the Internal Research Grant. Benjamin Golub gratefully acknowledges
ﬁnancial support from The Pershing Square Fund for Research on the Foundations of Human Behavior and
the National Science Foundation (SES-1658940, SES-1629446). Goyal gratefully acknowledges support from
the Wesley Clair Mitchell Visiting Professorship at Columbia University during Spring 2020.


---


between two individuals reﬂecting how strongly the action of one affects the marginal
returns experienced by the other. The effects may take the form of strategic complements
or strategic substitutes. In addition to standalone returns and incentive spillovers, there
may be positive or negative externalities imposed by network neighbors on each other. 1
Before this game is played, the planner can target some individuals and alter their standalone marginal returns from status quo levels. The cost of the intervention is increasing
in the magnitude of the change and is separable across individuals. The planner seeks to
maximize the utilitarian welfare under equilibrium play of the game, subject to a budget
constraint on the cost of the intervention. Our results characterize the optimal intervention policy, showing how it depends on the network, the nature of spillovers, the status
quo incentives, and the budget.
An intervention on one individual has direct and indirect effects on the incentives of
others. These effects depend on the network and on whether the game features strategic
substitutes or complements. For example, suppose the planner increases a given individual’s standalone marginal returns to effort, thereby increasing his effort. If actions are
strategic complements, this will push up the incentives of the targeted individual’s neighbors. That will increase the efforts of the neighbors of these neighbors, and so forth,
creating aligned feedback effects throughout the network. In contrast, under strategic
substitutes, the same intervention will discourage the individual’s neighbors from exerting effort. However, the effect on those neighbors’ neighbors will be positive—that is, in
the same direction as the effect on the targeted agent. This interplay between spillovers
and network structure makes targeting interventions a complex problem.
At the heart of our approach is a particular way to organize the spillover effects in terms
of the principal components, or eigenvectors, of the matrix of interactions. Any change in
the vector of standalone marginal returns can be expressed in a basis of these principal
components. This basis has three special properties: (a) when standalone marginal returns are exogenously changed in the direction of a principal component, the effect is
to change equilibrium actions in the same direction ; (b) the magnitude of the effect is a
multiple of the magnitude of the exogenous change, and the multiplier is determined by
an eigenvalue of the network corresponding to that principal component; (c) the principal components are orthogonal, so the effects along various principal components can be
treated separately. The three properties we have listed permit us to express the effect of
interventions on actions, and on welfare, in a way that facilitates a simple characterization
of optimal interventions.
Our main result, Theorem 1, characterizes the optimal intervention in terms of how
similar it is to various principal components—or, in other words, how strongly represented various principal components are in it.
2 Building on this characterization, Corollary 1 describes how the nature of the strategic interaction shapes which principal components ﬁgure most prominently in the optimal intervention. The principal components
can be ordered by their associated eigenvalues (from high to low). In games of strategic complements, the optimal intervention is, after a suitable normalization, most similar
to the ﬁrst principal component—the vector of individuals’ eigenvector centralities in the
1This framework encompasses a number of well-known economic examples from the literature: spillovers
in educational/criminal effort (Ballester, Calvó-Armengol, and Zenou (2006)), research collaboration among
ﬁrms (Goyal and Moraga-Gonzalez (2001)), local public goods ( Bramoullé and Kranton (2007)), investment
games and beauty contests (Angeletos and Pavan(2007), Morris and Shin (2002)), and peer effects in smoking
(Jackson, Rogers, and Zenou (2017)).
2We use the standard notion of cosine similarity: the similarity of two vectors is the cosine of the angle
between them in a plane they jointly deﬁne.


---


network of strategic interactions. It is then progressively less similar to principal components with smaller eigenvalues. In games of strategic substitutes, the order is reversed: the
optimal intervention is most similar to the last (lowest-eigenvalue) principal component.
The “higher” principal components capture the more global structure of the network:
this is important for taking advantage of the aligned feedback effects arising under strategic complementarities. The “lower” principal components capture the local structure of
the network: they help the planner to target the intervention so that it does not cause
crowding out between adjacent neighbors; this is an important concern when actions are
strategic substitutes.
We then turn to the study of simple optimal interventions, that is, ones where the relative intervention on the incentives of each node is determined by a single network statistic
of that node, and invariant to other primitives (such as status quo incentives). Propositions 1 and 2 show that, for large enough budgets, the optimal intervention is simple: in
games of strategic complements, the optimal intervention vector is proportional to the
ﬁrst principal component, while in games of strategic substitutes, it is proportional to the
last one.
3 Moreover, the network structure determines how large the budget must be for
optimal interventions to be simple. In games of strategic complements (substitutes), the
important statistic is the gap between the top (bottom) two eigenvalues of the network of
strategic interactions. When this gap is large, even at moderate budgets the intervention
is simple.
Theorem 1, our characterization of optimal interventions, is derived in a deterministic
setting where the planner knows the status quo standalone marginal returns of all individuals. Our methods can also be used to study optimal interventions assuming the planner
does not know these returns but knows only their distribution. Propositions 3 and 4 characterize optimal interventions in a stochastic setting. These show that suitable analogues
of the main insights extend: the order of the principal components corresponds to how
heavily they are represented in the optimal intervention.
We now place the paper in the context of the literature. The intervention problem we
study concerns optimal policy in the presence of externalities. Research over the past two
decades has deepened our understanding of the empirical structure of networks and the
theory of how networks affect strategic behavior.
4 This has led to the study of how policy
design should incorporate information about networks. Network interventions are currently an active subject of research not only in economics but also in related disciplines
such as computer science, sociology, and public health. 5 The main contribution of this
paper is methodological. It lies in (i) using the principal components approach to decompose the effect of an intervention on social welfare and (ii) using the structure afforded by
this decomposition to characterize optimal interventions. Of special interest is the close
3In similarity terms, this means that the optimal intervention has a cosine similarity of nearly 1 to the ﬁrst or
last principal component (depending on the case), and a similarity of nearly 0 to all other principal components.
4See, for example, Goyal, Moraga, and van der Leij (2006), Ballester, Calvó-Armengol, and Zenou (2006),
Bramoullé, Kranton, and d’Amours (2014), and Galeotti, Goyal, Jackson, Vega-Redondo, and Yariv(2010).
5For a general introduction to the subject, seeRogers (1983), Kempe, Kleinberg, and T ardos(2003), Borgatti
(2006), and V alente(2012). Within economics, a prominent early contribution is Ballester, Calvó-Armengol,
and Zenou (2006); recent contributions include Banerjee, Chandrasekhar, Duﬂo, and Duﬂo (2013), Belhaj,
Deroïan and Saﬁ (2020), Bloch and Querou (2013), Candogan, Bimpikis, and Ozdaglar (2012), Demange
(2017), Fainmesser and Galeotti (2017), Galeotti and Goyal (2009), Galeotti and Rogers (2013), Leduc, Jackson, and Johari (2017), and Akbarpour, Malladi, and Saberi (2020).


---


relation between the strategic structure of the game (whether it features strategic complements or substitutes) and the appropriate principal components to target.6
The rest of the paper is organized as follows. Section2 presents the optimal intervention
problem. Section 3 sets out how we apply a principal component decomposition to our
game. Section 4 characterizes optimal interventions. Section 5 studies a setting where the
planner has incomplete information about agents’ standalone marginal returns. Section6
concludes. The Appendix contains the proofs of the main results—those in Section4.T h e
Supplemental Material (Galeotti, Golub, and Goyal (2020)) presents the proofs of other
results and discusses a number of extensions.
## 2. THE MODEL
We consider a simultaneous-move game among individuals N ={ 1/commaori/periodori/periodori/periodori/commaorin},w h e r e
n ≥ 2. Individual i chooses an action, ai ∈ R. The vector of actions is denoted by a ∈ Rn.
The payoff to individuali depends on this vector,a, the network with adjacency matrixG,
and other parameters, as described below:
Ui(a/commaoriG) =ai
(
bi +β
∑
j∈N
gijaj
)
  
returns from own action
− 1
2a2
i

private costs
of own action
+Pi(a−i/commaoriG/commaorib)  
pure externalities
/periodori (1)
The private marginal returns, or beneﬁts, from increasing the action ai depend both on
i’s own action,ai, and on others’ actions. The coefﬁcientbi ∈ R corresponds to the part of
i’s marginal return that is independent of others’ actions, and is thus calledi’s standalone
marginal return. The contribution of others’ actions to i’s marginal return is given by the
term β∑
j∈N gijaj .H e r egij ≥ 0 is a measure of the strength of the interaction between i
and j; we assume that for every i ∈N, gii = 0—there are no self-loops in the network G.
The parameterβcaptures strategic interdependencies. Ifβ>0, then actions are strategic
complements; if β< 0, then actions are strategic substitutes. The function Pi(a−i/commaoriG/commaorib)
captures pure externalities—that is, spillovers that do not affect best responses. The ﬁrstorder condition for individual i’s action to be a best response is
ai =bi +β
∑
j∈N
gijaj/periodori
Any Nash equilibrium action proﬁle a∗ of the game satisﬁes
[I − βG]a∗ =b/periodori (2)
We now make two assumptions about the network and the strength of strategic
spillovers. Recall that the spectral radius of a matrix is the maximum of its eigenvalues’
absolute values.
ASSUMPTION 1: The adjacency matrix G is symmetric.7
6Appendix Section OA2.1 of the Supplemental Material (Galeotti, Golub, and Goyal(2020)) presents a discussion of the relationship between principal components and other network measures that have been studied
in the literature.
7We extend our analysis to more generalG in Supplemental Material Section OA3.2.


---


ASSUMPTION 2: The spectral radius of βGis less than 1,8 and all eigenvalues of G are
distinct.( The latter condition holds generically .)
Assumption 2 ensures that ( 2) is a necessary and sufﬁcient condition for each individual to be best-responding, and also ensures the uniqueness and stability of the Nash
equilibrium.9 Under these assumptions, the unique Nash equilibrium of the game can be
characterized by
a∗ =[I − βG]−1b/periodori (3)
The utilitarian social welfare at equilibrium is deﬁned as the sum of the equilibrium
utilities:
W(b/commaoriG) =
∑
i∈N
Ui
(
a∗/commaoriG
)
/periodori
The planner aims to maximize the utilitarian social welfare at equilibrium by changing
a vector of status quo standalone marginal returns ˆb to a vector b, subject to a budget
constraint on the cost of her intervention. The timing is as follows. The planner moves
ﬁrst and chooses her intervention, and then individuals simultaneously choose actions.
The planner’s incentive-targeting (IT) problem is given by
max
b
W(b/commaoriG)
s.t.: a∗ =[I − βG]−1b/commaori (IT)
K(b/commaoriˆb) =
∑
i∈N
(bi − ˆbi)2 ≤ C/commaori
where C is a given budget. The function K is an adjustment cost of implementing an
intervention.
The crucial features of the cost function are that it is separable across individuals and
increasing in the magnitude of the change to each individual’s incentives. We begin our
analysis with the simple functional form given above capturing these features, and examine robustness in the Supplemental Material. In Section OA3.3, we further discuss the
form of the adjustment costs and give extensions of the analysis to more general planner
cost functions. In Section OA3.4, we examine a setting in which a planner provides monetary payments to individuals that induce them to change their actions, and show that the
resulting optimal intervention problem has the same mathematical structure as the one
we study in our basic model.
We present two economic applications to illustrate the scope of our model. The ﬁrst
example is a classical investment game, and the second is a game of providing a local
public good.
E
XAMPLE 1—The Investment Game: Individual i makes an investmentai at a cost 1
2a2
i .
The private marginal return on that investment isbi +β∑
j∈N gijaj ,w h e r ebi is individual
8An equivalent condition is for |β|to be less than the reciprocal of the spectral radius of G.
9See Ballester, Calvó-Armengol, and Zenou (2006)a n dBramoullé, Kranton, and d’Amours (2014)f o rd e -
tailed discussions of this assumption and the interpretation of the solution given by (3).


---


i’s standalone marginal return and ∑
j∈N gijaj is the aggregate local effort. The utility ofi
is
Ui(a/commaoriG) =ai
(
bi +β
∑
j∈N
gijaj
)
− 1
2a2
i /periodori
The case with β> 0 reﬂects investment complementarities, as in Ballester, CalvóArmengol, and Zenou (2006). Here, an individual’s marginal returns are enhanced when
his neighbors work harder; this creates both strategic complementarities and positive externalities. The case of β< 0 corresponds to strategic substitutes and negative externalities; this can be microfounded via a model of competition in a market after the investment
decisions ai have been made, as in Goyal and Moraga-Gonzalez (2001). A planner who
observes the network of strategic interactions—for instance, which agents work together
on joint projects—can intervene by changing levels of monitoring or encouragement relative to a status quo level.
It can be veriﬁed that the equilibrium utilities,U
i(a∗/commaoriG), and the utilitarian social welfare at equilibrium, W(b/commaoriG), are as follows:
Ui
(
a∗/commaoriG
)
= 1
2
(
a∗
i
)2
and W(b/commaoriG) = 1
2
(
a∗)T
a∗/periodori
EXAMPLE 2—Local Public Goods: We next consider a local public goods problem in a
framework that follows the work of Bramoullé and Kranton (2007), Galeotti and Goyal
(2010), and Allouch (2015, 2017). In a local public goods problem, each agent makes a
costly contribution, which brings her closer to an ideal level of public goods but also raises
the levels enjoyed by her neighbors. Examples include (i) contributions to improve physical neighborhoods, such as residents clearing snow; 10 (ii) knowledge workers acquiring
non-rivalrous information (e.g., about job applicants) that can be shared with colleagues.
In example (i), the network governing spillovers is given by physical proximity, while in
example (ii), it is given by organizational overlap. We now elaborate on the nature of initial incentives and the interventions in the context of example (i). Agents receive some
level of municipal services at the status quo. They augment it with their own effort, and
beneﬁt (with a discount) from the efforts contributed by neighbors. A planner (say, a city
councilor) who observes the network structure of physical proximity among houses can
intervene to change the status quo allocation of services, tailoring it to improve incentives.
Formally, suppose that if each i contributes effort a
i to the public good, then the
amount of public good i experiences is
xi = ˜bi +ai + ˜β
∑
j∈N
gijaj/commaori
where 0< ˜β<1. The utility of i is
Ui(a/commaoriG) =− 1
2(τ− xi)2 − 1
2a2
i /commaori
where ˜bi <τ.
10Other examples include workers keeping areas on a factory ﬂoor clean and safe, and businesses in a retail
area contributing to the maintenance of their surroundings.


---


We now connect these formulas to the motivating descriptions. The optimal level of
public good in the absence of any costs is τ; this can be thought of as the maximum that
can be provided. Individual i has access to a base level ˜bi of the public good. Each agent
can expend costly effort,ai, to augment this base level to ˜bi +ai.I fi’s neighborj expends
effort, aj , then i has access to an additional ˜βgijaj units of the public good, where ˜β<1.
This is a game of strategic substitutes and positive externalities. Performing the change
of variables bi =[τ− bi]/2a n dβ=− ˜β/2 (with the status quo equal to ˆbi =[τ− ˜bi]/2)
yields a best-response structure exactly as in condition ( 2). The aggregate equilibrium
utility is W(b/commaoriG) =− (a∗)Ta∗.
All the settings discussed in Examples 1 and 2 share a technically convenient property:
PROPERTY A: The aggregate equilibrium utility is proportional to the sum of the
squares of the equilibrium actions, that is, W(b/commaoriG) =w ·(a∗)Ta∗ for some w ∈ R,w h e r e
a∗ is the Nash equilibrium action proﬁle.
Supplemental Material Section OA2.2 discusses a network beauty contest game inspired by Morris and Shin (2002)a n d Angeletos and Pavan (2007) which also satisﬁes
this property. While Property A facilitates analysis, it is not essential. Supplemental Material Section OA3.1 extends the analysis to cover important cases where this property
does not hold.
## 3. PRINCIP AL COMPONENTS
This section introduces a basis for the space of standalone marginal returns and actions
in which, under our assumptions on G, strategic effects and the planner’s objective both
take a simple form.
FACT 1: If G satisﬁes Assumption 1, then G =UΛUT, where:
1. Λis an n ×n diagonal matrix whose diagonal entries Λℓℓ =λℓ are the eigenvalues of G
(which are real numbers ), ordered from greatest to least : λ1 ≥ λ2 ≥···≥ λn.
2. U is an orthogonal matrix . The ℓth column of U, which we call uℓ, is a real eigenvector
of G, namely, the eigenvector associated to the eigenvalue λℓ, which is normalized so
that ∥uℓ∥= 1( in the Euclidean norm).
For genericG, the decomposition is uniquely determined, except that any column ofU
is determined only up to multiplication by −1.
An important interpretation of this diagonalization is as a decomposition into principal
components. First, consider the symmetric rank-one matrix that best approximates G in
the squared-error sense—equivalently, the vector u such that
∑
i/commaorij∈N
(gij − uiuj)2
is minimized. The minimizer turns out to be a scaling of the eigenvector u1.N o w ,i fw e
consider the “residual” matrix G(2) =G − u1(u1)T, we can perform the same type of decomposition on G(2) and obtain the second eigenvector u2 as the best rank-one approximation. Proceeding further in this way gives a sequence of vectors that constitute an


---


FIGURE 1.—(T op) Eigenvectors 2, 4, 6. (Bottom) Eigenvectors 10, 12, 14. Node shading represents the sign
of the entry, with the lighter shading (green) indicating a positive entry and the darker shading (red) indicating
a negative entry. Node area is proportional to the magnitude of the entry.
orthonormal basis. At each step, the next vector generates the rank-one matrix that “best
summarizes” the remaining structure in the matrix G.11
Figure 1 illustrates some eigenvectors/principal components of a circle network with 14
nodes, where links all have equal weight given by 1. For each eigenvector, the shading of a
node indicates the sign of the entry corresponding to that node in that eigenvector, while
the size of a node indicates the absolute value of that entry.
12 A general feature worth
noting is that the entries of the top eigenvectors (with smaller values of ℓ) are similar
among neighboring nodes, while the bottom eigenvectors (with larger values ofℓ)t e n dt o
be negatively correlated among neighboring nodes.13
3.1. Analysis of the Game Using Principal Components
For any vectorz ∈ Rn,l e tz =UTz. We will refer tozℓ as the projection ofz onto theℓth
principal component, or the magnitude of z in that component. Substituting the expression G =UΛUT into equation (2), which characterizes equilibrium, we obtain
[
I − βUΛUT]
a∗ =b/periodori
Multiplying both sides of this equation by UT gives us an analogue of (3 ) characterizing
the solution of the game:
[I − βΛ]a∗ =b ⇐⇒ a∗ =[I − βΛ]−1b/periodori
This system is diagonal, and theℓth diagonal entry of[I −βΛ]−1 is 1
1−βλℓ
. Hence, for every
ℓ ∈{ 1/commaori2/commaori/periodori/periodori/periodori/commaorin},
a∗
ℓ = 1
1 − βλℓ
bℓ/periodori (4)
11See Spielman (2007), especially Section 16.5.1, on this interpretation. For book-length treatments of spectral graph theory, see Cvetkovic, Cvetkovi´c, Rowlinson, and Simic (1997)a n dChung and Graham (1997).
12The circle network is invariant to rotations (cyclic permutations) of the nodes and so the eigenvectors here
are determined only up to a rotation.
13For formal treatments of this phenomenon, seeDavies, Gladwell, Leydold, and Stadler(2001)a n dUrschel
(2018).


---


The principal components of G constitute a basis in which strategic effects are easily described. The equilibrium action a∗
ℓ in the ℓth principal component of G is the product of
an ampliﬁcation factor (determined by the strategic parameter βand the eigenvalue λℓ)
andbℓ, which is simply the projection ofb onto that principal component. Under Assumption 2,f o ra l lℓ we have 1 − βλℓ > 0.14 Moreover, when β>0( β< 0), the ampliﬁcation
factor is decreasing (increasing) in ℓ.
We can also use (4) to give a formula for equilibrium actions in the original coordinates:
a∗
i =
n∑
ℓ=1
1
1 − βλℓ
uℓ
i
bℓ/periodori
We close with a deﬁnition that will allow us to describe optimal interventions in terms
of a standard measure of their similarity to various principal components.
DEFINITION 1: The cosine similarity of two nonzero vectors y and z is ρ(y/commaoriz) = y·z
∥y∥∥z∥ .
This is the cosine of the angle between the two vectors in a plane determined by y and
z.W h e nρ(y/commaoriz) = 1, the vector z is a positive scaling of y.W h e nρ(y/commaoriz) = 0, the vectors
y and z are orthogonal. When ρ(y/commaoriz) =− 1, the vector z is a negative scaling of y.
## 4. OPTIMAL INTERVENTIONS
This section develops a characterization of optimal interventions in terms of the principal components and studies their properties.
We begin by dispensing with a straightforward case of the planner’s problem. Recall
that under Property A, the planner’s payoff as a function of the equilibrium actions a∗ is
W(b/commaoriG) =w ·(a∗)Ta∗.I fw< 0, the planner wishes to minimize the sum of the squares of
the equilibrium actions. In this case, when the budget is large enough—that is,C ≥∥ ˆb∥2—
the planner can allocate resources to ensure that individuals have a zero target action by
setting bi = 0f o ra l li. It follows from the best-response equations that all individuals
choose action 0 in equilibrium, and so the planner achieves the ﬁrst-best. 15 The next assumption rules out the case in which the planner’s bliss point can be achieved, ensuring
that there is an interesting optimization problem.
A
SSUMPTION 3: Either w< 0 and C< ∥ˆb∥, or w> 0. Moreover, ˆbℓ ̸= 0 for each ℓ.
The last part of the assumption is technical; it holds for generic status quo vectors
ˆb (or generic G ﬁxing a status quo vector) and faciliates a description of the optimal
intervention in terms of similarity to the status quo vector.
Let b∗ solve the incentive-targeting problem ( IT), and let y∗ =b∗ − ˆb be the vector of
changes in individuals’ standalone marginal returns at the optimal intervention. Furthermore, let
αℓ = 1
(1 − βλℓ)2
14Assumption 2 on the spectral radius implies that βΛhas no entries larger than 1.
15In the local public goods application (recall Example 2), w =− 1, and so when C ≥∥ ˆb∥,t h eo p t i m a l
intervention satisﬁesb∗
i = 0. Recalling our change of variables there (bi =[τ− ˜bi]/2), the optimal intervention
in that case is to modify the endowment of each individual so that everyone accesses the optimal level of the
local public good without investing.


---


and note that a∗
ℓ = √αℓbℓ is the equilibrium action in the ℓth principal component of G
(see equation (4)).
THEOREM 1: Suppose Assumptions 1–3 hold and the network game satisﬁes Property A.
At the optimal intervention , the cosine similarity between y∗ and principal component uℓ(G)
satisﬁes the following proportionality :
ρ
(
y∗/commaoriuℓ(G)
)
∝ ρ
(ˆb/commaoriuℓ(G)
) wαℓ
μ− wαℓ
/commaoriℓ= 1/commaori2/commaori/periodori/periodori/periodori/commaorin/commaori(5)
where μ, the shadow price of the planner’s budget , is uniquely determined as the solution to
n∑
ℓ=1
( wαℓ
μ− wαℓ
) 2
ˆb
2
ℓ =C (6)
and satisﬁes μ>wαℓ for all ℓ, so that all denominators are positive .
We brieﬂy sketch the main argument here and interpret the quantities in the formula.
Deﬁne xℓ = (bℓ − ˆbℓ)/ˆbℓ as the change in bℓ, relative to ˆbℓ. By rewriting the principal’s
objective W(b/commaoriG) and budget constraints in terms of principal components and plugging
in the equilibrium condition (4), we can rewrite the maximization problem (IT)a s
max
x
n∑
ℓ=1
wαℓ(1 +xℓ)2 ˆb
2
ℓ
s.t.
n∑
ℓ=1
ˆb
2
ℓ
x2
ℓ ≤ C/periodori
If the planner allocates a marginal unit of the budget to changing xℓ, the condition for
equality of the marginal return and marginal cost (recalling thatμis the multiplier on the
budget constraint) is
2ˆb
2
ℓ ·wαℓ(1 +xℓ)  
marginal return
= 2ˆb
2
ℓ
·μxℓ
  
marginal cost
/periodori
It follows that wαℓ
μ−wαℓ
is exactly the value of xℓ at which the marginal return and the
marginal cost are equalized. 16 Rewriting xℓ in terms of cosine similarity, that equality
implies
wαℓ
μ− wαℓ
=x∗
ℓ =
y∗
ρ
(
y
∗/commaoriuℓ(G)
)
∥ˆb∥ρ
(ˆb/commaoriuℓ(G)
) /periodori
Rearranging this yields the proportionality expression (5 ) in the theorem. The Lagrange
multiplier μis determined by solving (6). Now, given μ, the similarities ρ(y∗/commaoriuℓ(G)) determine the direction of the optimal intervention y∗. The magnitude of the intervention
is found by exhausting the budget. Thus, Theorem 1 entails a full characterization of the
optimal intervention.
16It can be veriﬁed that, for every ℓ ∈{ 1/commaori/periodori/periodori/periodori/commaorin− 1},t h er a t i oxℓ/xℓ+1 is increasing (decreasing) in βfor the
case of strategic complements (substitutes): thus the intensity of the strategic interaction shapes the relative
importance of different principal components.


---


Next, we discuss the formula for the similarities given in expression ( 5). The similarity
between y∗ and uℓ(G) measures the extent to which principal component uℓ(G) is represented in the optimal interventiony∗.E q u a t i o n(5) tells us that this is proportional to two
factors. The ﬁrst factor, ρ(ˆb/commaoriuℓ(G)), measures the similarity between the ℓth principal
component and the status quo vector ˆb. This factor summarizes a status quo effect :h o w
much the initial condition inﬂuences the optimal intervention for a given budget. The intuition here is that if a given principal component is strongly represented in the status quo
vector of standalone incentives, then—because of the convexity of welfare in the principal
component basis—changes in that dimension have a particularly large effect.
The second factor,
wαℓ
μ−wαℓ
, is determined by two quantities: the eigenvalue corresponding
to uℓ(G) (via αℓ = 1
(1−βλℓ)2 ), and the budget C (via the shadow price μ). T o focus on this
second factor, wαℓ
μ−wαℓ
, we deﬁne the similarity ratio
r∗
ℓ = ρ
(
y∗/commaoriuℓ(G)
)
ρ
(ˆb/commaoriuℓ(G)
) /periodori (7)
Theorem 1 shows that, as we vary ℓ, the similarity ratio r∗
ℓ is proportional to wαℓ
μ−wαℓ
.I t
follows that the similarity ratio is greater, in absolute value, for the principal components
ℓ with greater αℓ. Intuitively, those are the components where the optimal intervention
makes the largest change relative to the status quo proﬁle of incentives. The ordering of
the r
∗
ℓ corresponds to the eigenvalues in a way that depends on the nature of strategic
spillovers:
COROLLAR Y1: Suppose Assumptions 1–3 hold and the network game satisﬁes Property A.
If the game is one of strategic complements (β>0), then |r∗
ℓ | is decreasing in ℓ; if the game is
one of strategic substitutes (β<0), then |r∗
ℓ | is increasing in ℓ.
In some problems, there may be a nonnegativity constraint on actions, in addition to the
constraints in problem (IT). As long as the status quo actionsˆb are positive, this constraint
will be respected for all C less than some ˆC, and so our approach will give information
about the relative effects on various components for interventions that are not too large.
4.1. Small and Large Budgets
The optimal intervention takes especially simple forms in the cases of small and large
budgets. From equation (6), we can deduce that the shadow priceμis decreasing inC.F o r
w> 0, it follows that an increase in C raises wαℓ
μ−wαℓ
. Moreover, the sequence of similarity
ratios becomes “steeper” as we increase C, in the following sense: if w> 0, for all ℓ, ℓ′
such that αℓ >αℓ′ , we have that r∗
ℓ/r∗
ℓ′ is increasing in C.17
PROPOSITION 1: Suppose Assumptions 1–3 hold and the network game satisﬁes Property A. Then the following hold:
1. As C → 0, in the optimal intervention,
r∗
ℓ
r∗
ℓ′
→ αℓ
αℓ′ .
2. As C →∞ , in the optimal intervention:
17Analogously, if w< 0, for all ℓ, ℓ′ such that αℓ >αℓ′ ,w eh a v et h a twαℓ
μ−wαℓ
and r∗
ℓ/r∗
ℓ′ are both decreasing
in C.


---


2a. Ifβ>0( the game features strategic complements), then the similarity of y∗ and the
ﬁrst principal component of the network tends to 1: ρ(y∗/commaoriu1(G)) → 1.
2b. If β<0( the game features strategic substitutes ), then the similarity of y∗ and the
last principal component of the network tends to 1: ρ(y∗/commaoriun(G)) → 1.
This result can be understood by recalling equation ( 5)i nT h e o r e m1. First, consider
the case of smallC. When the planner’s budget becomes small, the shadow priceμtends
to ∞ .18 Equation (5) then implies that the similarity ratio r∗
ℓ of the ℓth principal component (recall (7)) becomes proportional to αℓ. T urning now to the case whereC grows
large, the shadow price converges to wα1 if β> 0, and to wαn if β< 0 (by equation
(6)). Plugging this into equation (5 ), we ﬁnd that in the case of strategic complements,
the optimal intervention shifts individuals’ standalone marginal returns (very nearly) in
proportion to the ﬁrst principal component of G, so that y∗ →
√
Cu1(G). In the case
of strategic substitutes, on the other hand, the planner changes individuals’ standalone
marginal returns (very nearly) in proportion to the last principal component, namely,
y∗ →
√
Cun(G).19
Figure 2 depicts the optimal intervention in an example where the budget is large. We
consider an 11-node undirected network with binary links containing two hubs,L0 andR0,
that are connected by an intermediate node M; the network is depicted in Figure 2(A).
The numbers next to the nodes are the status quo standalone marginal returns; the budget is set toC = 500.20 Payoffs are as in Example1. For the case of strategic complements,
we set β= 0/periodori1, and for strategic substitutes, we set β=− 0/periodori1. Assumptions 1 and 2 are
satisﬁed and PropertyA holds. The top-left of Figure 2(B) illustrates the ﬁrst eigenvector,
and the top-right depicts the optimal intervention in a game with strategic complements.
The bottom-left of Figure 2(B) illustrates the last eigenvector, and the bottom-right depicts the optimal intervention when the game has strategic substitutes. The node size
represents the size of the intervention, |b
∗
i − ˆbi|; node shading represents the sign of the
FIGURE 2.—An example of optimal interventions with large budgets.
18As costs are quadratic, a small relaxation in the budget around zero can have a large impact on aggregate
welfare.
19When individuals’ initial standalone marginal returns are zero ( ˆb = 0), we can dispense with the approximations invoked for a large budget C. Assuming that G is generic, if ˆb = 0, then, for any C, the entire budget
is spent either (i) on changing b1 (if β>0) or (ii) on changing bn (if β<0).
20About 125 times larger than ∥ˆb∥2.


---


intervention, with the lighter shading (green) indicating a positive intervention and the
darker shading (red) indicating a negative intervention.
In line with part 2 of Proposition1, for largeC, the optimal intervention is guided by the
“main” component of the network. Under strategic complements, this is the ﬁrst (largesteigenvalue) eigenvector of the network, whose entries are individuals’ eigenvector centralities.
21 Intuitively, by increasing the standalone marginal return of each individual in
proportion to his eigenvector centrality, the planner targets the individuals in proportion
to their global contributions to strategic feedbacks, and this is welfare-maximizing.
Under strategic substitutes, optimal targeting is determined by the last eigenvector of
the network, corresponding to its smallest eigenvalue. This network component contains
information about the local structure of the network: it determines a way to partition the
set of nodes into two sets so that most of the links are across individuals in different sets.
22
The optimal intervention increases the standalone marginal returns of all individuals in
one set and decreases those of individuals in the other set. The planner wishes to target
neighboring nodes asymmetrically, as this reduces crowding-out effects that occur due to
the strategic substitutes property.
4.2. When Are Interventions Simple?
We have just seen examples illustrating how, with large budgets, the intervention is approximately simple in a certain sense: proportional to just one principal component. After formalizing a suitable notion of simplicity in our setting, the ﬁnal result in this section
characterizes how large the budget must be for such an approximation to be accurate.
D
EFINITION 2—Simple Interventions: An intervention is simple if, for all i ∈ N ,
• bi − ˆbi =
√
Cu1
i when the game has the strategic complements property (β>0),
• bi − ˆbi =
√
Cun
i when the game has the strategic substitutes property (β<0).
Such an intervention is called simple because the intervention on each node is—up to a
common scaling—determined by a single number that depends only on the network (via
its eigenvectors), and not on any other details such as the status quo incentives.23 Let W ∗
be the aggregate utility under the optimal intervention, and letWs be the aggregate utility
under the simple intervention.
PROPOSITION 2: Suppose w> 0, Assumptions 1 and 2 hold, and the network game satisﬁes Property A.
1. If the game has the strategic complements property , β> 0, then for any ϵ> 0, if C>
2∥ˆb∥2
ϵ ( α2
α1−α2
)2, then W ∗/W s < 1 +ϵ and ρ(y∗/commaori
√
Cu1)>
√
1 − ϵ.
2. If the game has the strategic substitutes property , β<0, then for any ϵ>0, if C>
2∥ˆb∥2
ϵ (
αn−1
αn−αn−1
)2, then W ∗/W s < 1 +ϵ and ρ(y∗/commaori
√
Cun)>
√
1 − ϵ.
21Supplemental Material Section OA2.1 presents a discussion of eigenvector centrality and how it compares
to centrality measures that turn out to be important in related targeting problems.
22The last eigenvector of a graph is useful in diagnosing the bipartiteness of a graph and its chromatic
number. Desai and Rao (1994) characterized the smallest eigenvalue of a graph and related it to a measure of
the graph’s bipartiteness. Alon and Kahale (1997) related the last eigenvector to a coloring of the underlying
graph—a labeling of nodes by a minimal set of integers such that no neighboring nodes share the same label.
23The deﬁnition also speciﬁes the interventions in more detail—that is, that they are proportional to the
appropriate uℓ
i . We could have instead left this ﬂexible in this deﬁnition of simplicity and speciﬁed the dependence on the network explicitly in Proposition 2.


---


Proposition 2 gives a condition on the size of the budget beyond which (a) simple interventions achieve most of the optimal welfare and (b) the optimal intervention is very similar to the simple intervention. This bound depends on the status quo standalone marginal
returns and on the structure of the network via
α2
α1−α2
(or a corresponding factor for “bottom” α’s).
We ﬁrst discuss the dependence of the bound on the status quo marginal returns. Observe that the ﬁrst term on the right-hand side of the inequality for C is proportional to
the squared norm of ˆb. This inequality is therefore easier to satisfy when this vector has
a smaller norm. The inequality is harder to satisfy when these marginal returns are large
and/or heterogeneous.
24
Next, consider the role of the network. Recall that αℓ =(1 − βλℓ)−2; thus if β> 0, the
term α2/(α1 − α2) of the inequality is large whenλ1 − λ2, the “spectral gap” of the graph,
is small. If β<0, then the term αn−1/(αn−1 − αn) is large when the difference λn−1 − λn,
which we call the “bottom gap,” is small.
We now examine what network features affect these gaps, and illustrate with examples,
depicted in Figure 3. The obstacle to the existence of simple optimal interventions is a
strong dependence on the status quo standalone marginal returns. This dependence will
be strong when two different principal components in the network offer the potential for
similar ampliﬁcation of an intervention. Which of these principal components receives
the planner’s focus will depend strongly on the status quo. In such networks, interventions will not be simple unless budgets are very large relative to status quo incentives. The
FIGURE 3.—Spectral gap, bottom gap, and optimal interventions.
24Recall that ∥ 1
n
ˆb∥2 is equal to the sum of ( 1
n
∑
i∈N
ˆbi)2 (the squared mean of the entries of b)a n dt h es u m
of squared deviations of the entries of the vector ˆb from their mean.


---


implication of Proposition 2 is that this sensitivity occurs when the appropriate gap in
eigenvalues (spectral gap or bottom gap) is small. Figure 3 illustrates the role of the network structure in shaping how the optimal intervention converges to the simple one (asC
increases). Under strategic complements, a large spectral gap ensures fast convergence.
Under strategic substitutes, a large bottom gap ensures fast convergence.
We now describe which more directly visible properties of network topology correspond
to small and large spectral gaps. First, consider the case of strategic complements. A standard fact is that the two largest eigenvalues can be expressed as follows:
λ1 = max
u:∥u∥=1
∑
i/commaorij∈N
gijuiuj/commaoriλ2 = max
u:∥ u∥=1
u·u1=0
∑
i/commaorij∈N
gijuiuj/periodori
Moreover, the eigenvector u1 is a maximizer of the ﬁrst problem, while u2 is a maximizer of the second; these are uniquely determined under Assumption 2. By the Perron–
Frobenius theorem, the ﬁrst eigenvector, u1, assigns the same sign—say, positive—to all
nodes in the network. Then the eigenvectoru2 must clearly assign negative values to some
of the nodes (as it is orthogonal tou1). In the network on the left side of Figure3(A), any
such assignment will result in many adjacent nodes having opposite-sign entries of u2;
as a result, many terms in the expression for λ2 will be negative, and λ2 will be considerably smaller than λ1, leading to a large spectral gap. In the network on the right side
of Figure 3(A), u2 turns out to have positive-sign entries for nodes in one community
and negative-sign entries for nodes in the other community. Because there are few edges
between the communities,λ2 turns out to be almost as large asλ1.T h i sy i e l d sas m a l ls p e c -
tral gap. These observations illustrate that the spectral gap is large when the network is
“cohesive,” and small when the network is, in contrast, divisible into nearly-disconnected
communities.
25 In light of this interpretation, our results imply that highly cohesive networks admit near-optimal interventions that are simple.
T urning next to strategic substitutes, recall that the smallest two eigenvalues, λn and
λn−1, can be written as follows:
λn = min
u:∥u∥=1
∑
i/commaorij∈N
gijuiuj/commaoriλn−1 = min
u:∥ u∥=1
u·un=0
∑
i/commaorij∈N
gijuiuj/periodori (8)
Moreover, the eigenvectorun is a maximizer of the ﬁrst problem, whileun−1 is a maximizer
of the second; these are uniquely determined under Assumption 2. This tells us thatλn is
low26 when the eigenvectorun = arg minu:∥u∥=1
∑
i/commaorij∈N gijuiuj (corresponding toλn) assigns
opposite signs to most pairs of adjacent nodes. In other words, the last eigenvalue is small
when nodes can be partitioned into two sets and most of the connections are across sets.
Thus, λ
n is minimized in a bipartite graph. The second-smallest eigenvalue of G reﬂects
the extent to which the next-best eigenvector (orthogonal to un) is good at solving the
same minimization problem. Hence, the bottom gap of G is small when there are two
orthogonal ways to partition the network into two sets so that, either way, the “quality” of
the bipartition, as measured by ∑
i/commaorij∈N gijuiuj , is similar.
25See Hartﬁel and Meyer (1998), Levin, Peres, and Wilmer (2009), and Golub and Jackson (2012)f o rd i s -
cussions and further citations to the literature on spectral gaps.
26The eigenvalue is in fact negative, as a consequence of the assumption thatgii = 0 for alli:T h et r a c eo fG
is zero, and therefore its eigenvalues sum to 0. By the Perron–Frobenius theorem, the maximum eigenvalue of
the nonnegative matrix G is positive, so the minimum one must be negative.


---


We illustrate part 2 of Proposition2 with a comparison of the two graphs in Figure3(C).
The left-hand graph is bipartite: the last eigenvalue isλn =− 3 and the second-last eigenvalue is λn−1 =− 1/periodori64. In contrast, the graph on the right of Figure 3(C) has a bottom
eigenvalue λn =− 2/periodori62, and a second-lowest eigenvalue of λn−1 =− 2/periodori30. This yields a
much smaller bottom gap. 27 This difference in bottom gaps is reﬂected in the nature of
optimal interventions shown in Figure 3(D). In the graph with large bottom gap, the optimal intervention puts most of its weight on the eigenvector un even for relatively small
budgets. T o achieve a similar convergence to simplicity requires a much larger budget
when the bottom gap is small: the second-smallest eigenvector un−1 receives substantial
weight even for fairly large values of the budget C.
We conclude by noting the inﬂuence of the status quo standalone marginal returns in
shaping optimal interventions for small budgets. For a small budgetC, the cosine similarity of the optimal intervention for non-main network components can be higher than the
one for the main component. This is true when the status quo ˆb is similar to some of the
non-main network components; see Figures 3(B) and Figure 3(D).
## 5. INCOMPLETE INFORMATION
In the basic model, we assumed that the planner knows the standalone marginal returns
of every individual. This section extends the analysis to settings where the planner does
not know these parameters. As before, we focus on network games that satisfy PropertyA.
Formally, ﬁx a probability space (Ω/commaoriF/commaoriP). The planner’s probability distribution over
states is given by P. The planner has control over the random vector (r.v.) B—that is,
af u n c t i o nB :Ω→ Rn. The cost of the intervention depends on the choice of B.T h e r e
is a function K that gives the cost K(B) of implementing the random variable B.28 A
realization of the random vector is denoted by b. This realization is common knowledge
among individuals when they choose their actions. Thus, the game individuals play is one
of complete information.29
We solve the following incomplete-information intervention problem:
choose r.v. B to maximize E
[
W(b;G)
]
s.t. [I − βG]a∗ =b/commaori (IT-G)
K(B) ≤ C/periodori
Note that the intervention problem ( IT) under complete information is the special case
of a degenerate r.v. B: one in which the planner knows the vector of standalone marginal
returns exactly and implements a deterministic adjustment relative to it.
T o guide our modeling of the cost of intervention, we now examine the features of
the distribution of B that matter for aggregate welfare. For network games that satisfy
27Intuitively, because un does not correspond to a perfect bipartition, it is easier for a vector orthogonal to
un to achieve a similarly low value of ∑
i/commaorij∈N gijuiuj .
28The domain of this function is the set of all random vectors taking values in Rn deﬁned on our probability
space.
29It is possible to go further and allow for incomplete information among the individuals about each
other’s bi. We do not pursue this substantial generalization here; see Golub and Morris (2020)a n dLambert,
Martini, and Ostrovsky (2018) for analyses in this direction.


---


Property A,w ec a nw r i t e
E
[
W(b;G)
]
=wE
[(
a∗)T
a∗]
=wE
[(
aT)∗(
a∗)]
=w
n∑
ℓ=1
αℓ
(
E[bℓ]2 + Va r[bℓ]
)
/periodori(9)
Note the change from the ordinary to the principal component basis in the second step.
In words, welfare is determined by the mean and variance of the realized componentsbℓ;
these in turn are determined by the ﬁrst and second moments of the chosen random
variable
B. In view of this, we will consider intervention problems where the planner can
modify the mean and the covariance matrix of B, and the cost of intervention depends
only on these modiﬁcations.30
5.1. Mean Shifts
We ﬁrst consider an intervention where there is an arbitrarily distributed vector of status quo standalone marginal returns and the planner’s intervention shifts it in a deterministic way. Formally, ﬁx a random variable ˆB, called the status quo, with typical realization ˆb. The planner’s policy is given by b = ˆb +y,w h e r ey ∈ Rn is a deterministic vector.
We denote the corresponding random variable by By. In terms of interpretation, note
that implementing this policy does not require knowing ˆb as long as the planner has an
instrument that shifts incentives.
ASSUMPTION 4: The cost of implementing r.v. By is
K(By) =
∑
i∈N
y2
i /commaori
and K(B) is ∞ for any other random variable .
In contrast to the analysis of Theorem 1, the vector ˆb is a random variable. But we take
the analogue of the cost function used there, noting that in the deterministic setting (see
(IT)), this formula held with y =b − ˆb.
PROPOSITION 3: Consider problem (IT-G), with the cost of intervention satisfying Assumption 4. Suppose Assumptions 1 and 2 hold and the network game satisﬁes Property A.
The optimal intervention policy B∗ is equal to By∗, where y∗ is the optimal intervention in the
deterministic problem with b = E[ˆb] taken as the status quo vector of standalone marginal
returns.
5.2. Intervention on V ariances
We next consider the case where the planner faces a vector of means, ﬁxed at ¯b,a n d ,
subject to that, can choose any random variable B. It can be seen from (9 ) that, in this
class of mean-neutral interventions, the expected welfare of an intervention B depends
30This reduction is justiﬁed as follows: since only the ﬁrst two moments of standalone marginal returns affect
equilibrium welfare, the planner should choose the cost-minimizing way to achieve a desired combination of
these. We may take the cost of a given intervention to be the corresponding minimizer.


---


only on the variance–covariance matrix of B. Thus, the planner effectively faces the problem of intervening on variances, which we analyze for all cost functions satisfying certain
symmetries.
ASSUMPTION 5: The cost function satisﬁes two properties :( a) K(B) =∞ if E[b]̸ = ¯b;
(b)K(B) =K( ˜B) if ˜b− ¯b =O(b− ¯b), whereO is an orthogonal matrix.( Analogously to our
other notation, we use ˜b for realizations of ˜B.)
Part (a) is a restriction on feasible interventions, namely, a restriction to interventions
that are mean-neutral. Part (b) means that rotations of coordinates around the mean
do not affect the cost of implementing a given distribution. This assumption gives the
cost a directional neutrality, which ensures that our results are driven by the beneﬁts
side rather than by asymmetries operating through the costs. For an example where the
assumption is satisﬁed, let Σ
B be the variance–covariance matrix of the random variable
B. In particular, σB
ii is the variance of bi. Suppose that the cost of implementing B with
E[b]= ¯b is a function of the sum of the variances of the bi:
K(B) =
⎧
⎪⎨
⎪⎩
φ
( ∑
∈N
σB
ii
)
if E[b]= ¯b/commaori
∞ otherwise/periodori
(10)
The cost function ( 10) satisﬁes part (a) of Assumption 5. Moreover, it satisﬁes part (b)
of Assumption 5 because ∑
i∈N σB
ii = traceΣB; this trace is the sum of the eigenvalues of
ΣB, which is invariant to the transformation deﬁned in part (b).31
PROPOSITION 4—V ariance Control: Consider problem (IT-G) with a cost of intervention
satisfying Assumption 5. Suppose Assumptions 1 and 2 hold and the network game satisﬁes
Property A. Let the optimal intervention be B∗, and let b∗ be a typical realization. We have the
following:
1. Suppose the planner likes variance (i.e., in (9),w> 0). If the game has strategic complements (β>0), then Va r(uℓ(G) ·b∗) is weakly decreasing in ℓ; if the game has strategic
substitutes (β<0), then Va r(uℓ(G) ·b∗) is weakly increasing in ℓ.
2. Suppose the planner dislikes variance (i.e., w< 0). If the game has strategic complements (β> 0), then Va r(uℓ(G) ·b∗) is weakly increasing in ℓ; if the game has strategic
substitutes (β<0), then Va r(uℓ(G) ·b∗) is weakly decreasing in ℓ.
We now provide the intuition for Proposition 4. Shocks to individuals’ standalone
marginal returns create variability in the players’ equilibrium actions. The assumption
that the intervention is mean-neutral (part (a) of Assumption 5) leaves the planner to
control only the variances and covariances of these marginal returns with her intervention. Hence, the solution to the intervention problem describes what the planner should
do to induce second moments of the action distribution that maximize ex ante expected
welfare.
Suppose ﬁrst that investments are strategic complements. Then a perfectly correlated
(random) shock in individual standalone marginal returns is ampliﬁed by strategic interactions. In fact, the type of shock that is most amplifying (at a given size) is the one that
31When we look at the variance–covariance matrix of˜b deﬁned by ˜b− ¯b =O(b− ¯b), the variance–covariance
matrix becomes OΣOT, and this has the same eigenvalues and therefore the same trace.


---


is perfectly correlated across individuals: a common deviation from the mean is scaled
by the vector u1—the individuals’ eigenvector centralities. Such shocks are exactly what
b∗
1 =u1(G) ·b∗ captures. Hence, this is the dimension of volatility that the planner most
wants to increase if she likes variance in actions (w> 0) and most wants to decrease if she
dislikes variance in actions (w< 0).
If investments are strategic substitutes, then a perfectly correlated shock does not create a lot of variance in actions: the ﬁrst-order response of all individuals to an increase
in their standalone marginal returns is to increase investment, but that in turn makes all
individuals decrease their investment somewhat because of the strategic substitutability
with their neighbors. Hence, highly positively correlated shocks do not translate into high
volatility. The shock proﬁles (of a ﬁxed norm) that create the most variability in equilibrium actions are actually the ones in which neighbors have negatively correlated shocks.
A planner that likes variance in actions will then prioritize such shocks. Because the last
eigenvector of the system has entries that are as different as possible across neighbors,
this is exactly the type of volatility that will be most ampliﬁed, and this is what the planner
will focus on most.
E
XAMPLE 3—Illustration in the Case of the Circle: Figure 1 depicts six of the eigenvectors/principal components of a circle network with 14 nodes. The ﬁrst principal component is a positive vector and so
B projected on u1(G) captures shocks that are positively
correlated across all players. The second principal component (top left panel of Figure1)
splits the graph into two sides, one with positive entries and the other with negative entries. Hence, B projected on u2(G) captures shocks that are highly positively correlated
on each side of the circle network, with the two opposite sides of the circle being anticorrelated. As we move along the sequence of eigenvectors uℓ, we can see that B projected on the ℓth eigenvector represents patterns of shocks that “vary more” across the
network. At the extreme,B projected onu14(G) (bottom-right panel of Figure1)c a p t u r e s
the component of shocks that is perfectly anti-correlated across neighbors.32
## 6. CONCLUDING REMARKS
We have studied the problem of a planner who seeks to optimally target incentive
changes in a network game. Our framework allows for a broad class of strategic and nonstrategic spillovers across neighbors. The main contribution of the paper is methodological: we show that principal components of the network of interaction provide a useful
basis for analyzing the effects of an intervention. This decomposition leads to our main
result: there is a close connection between the strategic properties of the game (whether
actions are strategic complements or substitutes) and the weight that different principal
components receive in the optimal intervention. T o develop these ideas in the simplest
way, we have focused on a model in which the matrix of interaction is symmetric, the
costs of intervention are quadratic, and the intervention itself takes the form of altering
the standalone marginal returns of actions. In the Supplemental Material, we relax these
restrictions and develop extensions of our approach to non-symmetric matrices of interaction and to more general costs of intervention, including a model where interventions
occur via monetary incentives for activity. We also relax PropertyA, a technical condition
which facilitated our basic analysis, and cover a more general class of externalities.
32As usual in this example, a generic G will not be perfectly symmetric and so a particular orientation of
these eigenvectors will be selected.


---


We brieﬂy mention two further applications. In some circumstances, the planner seeks
a budget-balanced tax/subsidy scheme in order to improve the economic outcome. In
an oligopoly market, for example, a planner could tax some suppliers, thereby increasing their marginal costs, and then use that tax revenue to subsidize other suppliers. The
planner will solve a problem similar to the one we have studied here, with the important
difference that she will face a different constraint—namely, a budget-balance constraint.
In ongoing work, Galeotti, Golub, Goyal, T alamàs, and T amuz(2020) show that the principal component approach that we employed in this paper is useful in deriving the optimal
taxation scheme and, in turn, in determining the welfare gains that can be achieved via
tax/subsidy interventions in supply chains.
33
We have focused on interventions that alter the standalone marginal returns of individuals. Another interesting problem is the study of interventions that alter the matrix of
interaction. We hope this paper stimulates further work along these lines.
APPENDIX: P
ROOFS
PROOF OF THEOREM 1:W e w i s h t o s o l v e
max
b
waTa
s.t.: [I − βG]a =b/commaori
∑
i∈N
(bi − ˆbi)2 ≤ C/periodori
We transform the maximization problem into the basis given by the principal components
of G. T o this end, we ﬁrst rewrite the cost and the objective in the principal components
basis, using the fact that norms do not change under the orthogonal transformation U
T.
(The norm symbol ∥·∥ always refers to the Euclidean norm.) Letting y =b − ˆb,
K(b/commaoriˆb) =
∑
i∈N
y2
i =∥y∥2
2 =
n∑
ℓ=1
y2
ℓ
and
waTa =w∥a∥2 =w∥a∥2 =waTa/periodori
By recalling that, in equilibrium, a∗ =[ I − βΛ]−1b, and using the deﬁnition αℓ =
1
(1−βλℓ(G))2 , the intervention problem (IT) can be rewritten as
max
b
w
n∑
ℓ=1
αℓb2
ℓ (IT-PC)
s.t.
n∑
ℓ=1
y2
ℓ ≤ C/periodori
33In a recent paper, Gaitonde, Kleinberg and T ardos(2020) use spectral methods to study interventions that
polarize opinions in a social network.


---


We now transform the problem so that the control variable is x where xℓ = yℓ/ˆbℓ.W e
obtain
max
x
w
∑
ℓ = 1nαℓ(1 +xℓ)2 ˆb
2
ℓ
s.t.
n∑
ℓ=1
ˆb
2
ℓ
x2
ℓ ≤ C/periodori
Note that, for all ℓ, αℓ are well-deﬁned (by Assumption 1) and strictly positive (by
genericity of G). This has two implications.34
First, at the optimal solutionx∗, the resource constraint problem must bind. T o see this,
note that Assumption 3 says that eitherw> 0, orw< 0a n d∑n
ℓ=1
ˆb
2
ℓ >C . Suppose that at
the optimal solution, the constraint does not bind. Then, without violating the constraint,
we can slightly increase or decrease any xℓ.I f w> 0 (resp. w< 0), the increase or the
decrease is guaranteed to increase (resp. decrease) the corresponding(xℓ + 1)2 (since the
αℓ are all strictly positive).
Second, we show that the optimal solution x∗ satisﬁes x∗
ℓ ≥ 0 for every ℓ if w> 0, and
x∗
ℓ
∈[ −1/commaori0] for every ℓ if w< 0. Suppose w> 0a n d ,f o rs o m eℓ, x∗
ℓ
< 0. Then [−x∗
ℓ
+
1]2 > [x∗
ℓ + 1]2.S i n c ew> 0 and every αℓ is positive, we can raise the aggregate utility
without changing the cost by ﬂipping the sign of x∗
ℓ . Analogously, suppose w< 0. It is
clear that if x∗
ℓ
< −1, then by setting xℓ =− 1, the objective improves and the constraint
is relaxed; hence, at the optimum, x∗
ℓ
≥− 1. Suppose next that xℓ > 0f o rs o m eℓ.T h e n
[−x∗
ℓ
+ 1]2 < [x∗
ℓ
+ 1]2.S i n c ew< 0 and every αℓ is positive, we can improve the value of
the objective function without changing the cost by ﬂipping the sign of x∗
ℓ .
We now complete the proof. Observe that the Lagrangian corresponding to the maximization problem is
L =w
n∑
ℓ=1
αℓ(1 +xℓ)2 ˆbℓ +μ
[
C −
n∑
ℓ=1
ˆb
2
ℓx2
ℓ
]
/periodori
T aking our observation above that the constraint is binding at x =x∗, together with the
standard results on the Karush–Kuhn–T ucker conditions, the ﬁrst-order conditions must
hold exactly at the optimum with a positive μ:
0 = ∂L
∂xℓ
= 2ˆb
2
ℓ
[
wαℓ
(
1 +x∗
ℓ
)
− μx∗
ℓ
]
= 0/periodori (11)
We take a generic ˆb such that ˆbℓ ̸= 0f o ra l lℓ. If, for some ℓ,w eh a dμ=wαℓ, then the
right-hand side of the second equality in (11) would be 2 ˆb
2
ℓwαℓ, which, by the generic assumption we just made and the positivity ofαℓ, would contradict (11). Thus, the following
holds with a nonzero denominator:
x∗
ℓ = wαℓ
μ− wαℓ
/commaori
34Note that if Assumption3 does not hold (i.e.,w< 0a n d∑n
ℓ=1
ˆb
2
ℓ ≤ C), then the optimal solution isx∗
ℓ =− 1
for all ℓ. This is what we ruled out with Assumption 3, before Theorem 1.


---


and the Lagrange multiplier μis therefore pinned down by
n∑
ℓ=1
w2 ˆb
2
ℓ
( αℓ
μ− wαℓ
) 2
=C/periodori
Note ﬁnally that
ρ
(
y∗/commaoriuℓ(G)
)
= y∗ ·uℓ(G)y∗

u
ℓ(G)


=
y
∗
ℓ√
C
=
ˆbℓx∗
ℓ√
C
= ∥ˆb∥√
C
ρ
(ˆb/commaoriuℓ(G)
)
x∗
ℓ ∝ℓ ρ
(ˆb/commaoriuℓ(G)
)
x∗
ℓ
/periodoriQ.E.D.
PROOF OF PROPOSITION 1: Part 1. From expression ( 6)o fT h e o r e m1,i tf o l l o w st h a ti f
C → 0, then μ→∞ . The result follows by noticing that
r∗
ℓ
r∗
ℓ′
= αℓ
αℓ′
μ− wα′
ℓ
μ− wαℓ
/periodori
Part 2. Suppose thatβ>0. Using the derivation of the last part of the proof of Theorem1,
we write
ρ
(
y∗/commaoriuℓ(G)
)
= ∥ˆb∥√
C
ρ
(ˆb/commaoriuℓ(G)
)
x∗
ℓ/commaori
with x∗
ℓ = wαℓ
μ−wαℓ
. From expression (6)o fT h e o r e m1, it follows that if C →∞ , then μ→
wα1. This implies thatx∗
ℓ
→ αℓ
α1−αℓ
for allℓ ̸= 1. As a result, ifC →∞ , thenρ(y∗/commaoriuℓ(G)) →
0f o ra l lℓ ̸= 1. Furthermore, we can rewrite expression (6)o fT h e o r e m1 as
n∑
ℓ=1
(
∥ˆb∥ρ
(ˆb/commaoriuℓ(G)
) x∗
ℓ√
C
) 2
= 1/commaori
and therefore
lim
C→∞
n∑
ℓ=1
(
∥ˆb∥ρ
(ˆb/commaoriuℓ(G)
) x∗
ℓ√
C
) 2
= lim
C→∞
(
∥ˆb∥ρ
(ˆb/commaoriu1(G)
) x∗
1
√
C
) 2
= 1/commaori
where the ﬁrst equality follows because x∗
ℓ → αℓ
α1−αℓ
for all ℓ ̸= 1. The proof for the case
of β<0 follows the same steps, with the only exception that if C →∞ , then μ→ wαn.
Q.E.D.
PROOF OF PROPOSITION 2: We ﬁrst prove the result on welfare and then turn to the
result on cosine similarity.
Welfare. Consider the case of strategic complementarities,β>0. Deﬁne by ˜x the simple intervention, and note that ˜x1 =
√
C/ ˆb1 and that ˜xℓ = 0f o ra l lℓ> 1. The aggregate
utility obtained under the simple intervention is
Ws =
n∑
ℓ=1
ˆb
2
ℓαℓ(1 + ˜xℓ)2 = ˆb
2
1
α1 ˜x1(˜x1 + 2) +
n∑
ℓ=1
αℓ ˆb
2
ℓ
/periodori


---


The aggregate utility at the optimal intervention is
W ∗ =
n∑
ℓ=1
ˆb
2
ℓαℓ
(
1 +x∗
ℓ
)2
= ˆb
2
1α1x∗
1
(
x∗
1
+ 2
)
+
n∑
ℓ=2
ˆb
2
ℓαℓx∗
ℓ
(
x∗
ℓ
+ 2
)
+
n∑
ℓ=1
αℓ ˆb
2
ℓ/periodori
Hence, letting D = ˆb
2
1α1 ˜x1(˜x1 + 2) + ∑n
ℓ=1 αℓ ˆb
2
ℓ,
W ∗
Ws =
ˆb
2
1
α1x∗
1
(
x∗
1
+ 2
)
+
n∑
ℓ=1
αℓ ˆb
2
ℓ
D +
n∑
ℓ=2
ˆb
2
ℓ
αℓx∗
ℓ
(
x∗
ℓ
+ 2
)
D
≤ 1 +
n∑
ℓ=2
ˆb
2
ℓαℓx∗
ℓ
(
x∗
ℓ
+ 2
)
D as ˜x1 ≥ x∗
1
≤ 1 +
n∑
ℓ=2
ˆb
2
ℓαℓx∗
ℓ
(
x∗
ℓ
+ 2
)
ˆb
2
1α1 ˜x2
1
terms inD are positive
= 1 +
n∑
ℓ=2
ˆb
2
ℓαℓx∗
ℓ
(
x∗
ℓ
+ 2
)
α1C b2
1 ˜x2
1 =C; see below
≤ 1 + 2α1 − α2
α1
∥ˆb∥2
C
( α2
α1 − α2
) 2
see calculation below
≤ 1 + 2∥ˆb∥2
C
( α2
α1 − α2
) 2
/periodori
The fact b2
1 ˜x2
1 = C, used above, follows because the simple policy allocates the entire
budget to changing b1. The inequality after that statement follows because
n∑
ℓ=2
ˆb
2
ℓαℓx∗
ℓ
(
x∗
ℓ
+ 2
)
≤ α2
n∑
ℓ=2
ˆb
2
ℓx∗
ℓ
(
x∗
ℓ
+ 2
)
ordering of the αℓ
≤ α2x∗
2
(
x∗
2
+ 2
) n∑
ℓ=2
ˆb
2
ℓ Corollary 1
≤ α2
wα2
μ− wα2
( wα2
μ− wα2
+ 2
) n∑
ℓ=2
ˆb
2
ℓ
Theorem 1
≤ α2
wα2
wα1 − wα2
( wα2
wα1 − wα2
+ 2
)
∥ˆb∥2
=
( α2
α1 − α2
) 2
(2α1 − α2)∥ˆb∥2/periodori


---


Hence, the inequality
C> 2∥ˆb∥2
ϵ
( α2
α1 − α2
) 2
is sufﬁcient to establish that W ∗
Ws < 1 +ϵ. The proof for the case of strategic substitutes
follows the same steps; the only difference is that we useαn instead ofα1 andαn−1 instead
of α2.
Cosine similarity. We now turn to the cosine similarity result. We focus on the case of
strategic complements. The proof for the case of strategic substitutes is analogous. We
start by writing a useful explicit expression for ρ
(
/Delta1b∗/commaori
√
Cu1)
:
ρ
(
/Delta1b∗/commaori
√
Cu1)
=
(
b∗ − ˆb
)
·
(√
Cu1)
b∗ − ˆb


√
Cu1
 =
(
b
∗ − ˆb
)
·
(
u1)
√
C
/commaori (12)
where the last equality follows because, at the optimum, ∥b∗ − ˆb∥2 =C. At the optimal
intervention, by Theorem 1,
b∗
ℓ − ˆbℓ = wαℓ
μ− wαℓ
ˆbℓ;
now, using the deﬁnition b =UTb, we have that
b∗
i − ˆbi =w
n∑
ℓ=1
ui
ℓ
αℓ
μ− wαℓ
ˆbℓ
and therefore
(
b∗ − ˆb
)
·u1 =
∑
i
n∑
ℓ=1
u1
i uℓ
i
wαℓ
μ− wαℓ
ˆbℓ =
n∑
ℓ=1
wαℓ
μ− wαℓ
ˆbℓ
(
u1 ·uℓ)
= wα1
μ− wα1
ˆb1/periodori
Hence, using this in equation (12), we can deduce that
ρ
(
/Delta1b∗/commaoriu1)
= 1√
C
wα1
μ− wα1
ˆb1 ≥
√
1 − ϵ iff
( wα1
μ− wα1
) 2
ˆb
2
1 − C(1 − ϵ) ≥ 0/periodori(13)
We now claim that the inequality in the above display after the “if and only if” follows
from our hypothesis that
C> 2∥ˆb∥2
ϵ
( α2
α1 − α2
) 2
/periodori
This claim is established by the following lemma.
LEMMA 1: Assume
C> 2∥ˆb∥2
ϵ
( α2
α1 − α2
) 2
/periodori


---


Then
( wα1
μ− wα1
) 2
ˆb
2
1 ≥ C(1 − ϵ)/periodori (14)
PROOF OF LEMMA 1: Note that
C> 2∥ˆb∥2
ϵ
( α2
α1 − α2
) 2
=⇒ ϵC >∥ˆb∥2
( α2
α1 − α2
) 2
/commaori
and therefore
C(1 − ϵ)<C −∥ ˆb∥2
( α2
α1 − α2
) 2
/periodori (15)
But then we have the following chain of statements, explained immediately after the display:
( wα1
μ− wα1
) 2
ˆb
2
1 − C(1 − ϵ) ≥
( wα1
μ− wα1
) 2
ˆb
2
1
− C +∥ ˆb∥2
( α2
α1 − α2
) 2
=
( wα1
μ− wα1
) 2
ˆb
2
1 −
n∑
ℓ=1
( wαℓ
μ− wαℓ
) 2
ˆb
2
ℓ
+∥ ˆb∥2
( α2
α1 − α2
) 2
=∥ ˆb∥2
( α2
α1 − α2
) 2
−
n∑
ℓ=2
( wαℓ
μ− wαℓ
) 2
ˆb
2
ℓ
=
( α2
α1 − α2
) 2 n∑
ℓ=1
ˆb
2
ℓ −
n∑
ℓ=2
( wαℓ
μ− wαℓ
) 2
ˆb
2
ℓ
> 0/periodori
The ﬁrst inequality follows from substituting the upper bound on C(1 − ϵ), statement
(15) above, which we derived from our initial condition on C. The equality after that
follows by substituting the condition on the binding budget constraint at the optimum,
which we derived in Theorem 1. The next equality follows by isolating the term for the
ﬁrst component in the summation and by noticing that that cancels with the ﬁrst term. The
next equality follows by noticing that ∥ˆb∥2 =∥ ˆb∥2. The ﬁnal inequality follows because,
from the facts that μ>w α1 and that α1 >α2 > ··· >αn, we can deduce that for each
ℓ> 1,
wαℓ
μ− wαℓ
< wαℓ
wα1 − wαℓ
= αℓ
α1 − αℓ
< α2
α1 − α2
/periodori Q.E.D.
This concludes the proof of Proposition 2. Q.E.D.
## REFERENCES
AKBARPOUR,M . ,S .MALLADI, AND A. SABERI (2020): “Just a Few Seeds More: V alue of Network Information
for Diffusion” Report, Graduate School of Business, Stanford University. [2447]
ALLOUCH, N. (2015): “On the Private Provision of Public Goods on Networks,” Journal of Economic Theory,
157, 527–552. [2450]
(2017): “ Aggregation in Networks,” Discussion Paper 1718, School of Economics, University of Kent.
[2450]


---


ALON,N . ,AND N. KAHALE (1997): “ A Spectral T echnique for Coloring Random 3-Colorable Graphs,”SIAM
Journal on Computing, 26, 1733–1748. [2457]
ANGELETOS,G . - M . ,AND A. PAVAN (2007): “Efﬁcient Use of Information and Social V alue of Information,”
Econometrica, 75, 1103–1142. [2446,2451]
BALLESTER,C . ,A .CALVÓ-ARMENGOL, AND Y. ZENOU (2006): “Who’s Who in Networks. Wanted: The Key
Player,” Econometrica, 74, 1403–1417. [2446,2447,2449,2450]
BANERJEE,A . ,A .G .C HANDRASEKHAR,E .D UFLO, AND M. O. D UFLO (2013): “The Diffusion of Microﬁnance,” Science, 341, 1236498. [2447]
BELHAJ,M . ,F .D EROÏAN, AND S. SAFI (2020): “T argeting in Networks under Costly Agreements,” Report,
Aix-Marseille University. [2447]
BLOCH,F . ,AND N. QUEROU (2013): “Pricing in Social Networks,”Games and Economic Behavior, 80, 263–281.
[2447]
BORGATTI, S. (2006): “Identifying Sets of Key Players in a Social Network,” Computational and Mathematical
Organization Theory, 12, 21–34. [2447]
BRAMOULLÉ,Y . , AND R. KRANTON (2007): “Public Goods in Networks,” Journal of Economic Theory, 135,
478–494. [2446,2450]
BRAMOULLÉ,Y . ,R .KRANTON, AND M. D’AMOURS (2014): “Strategic Interaction and Networks,” The American Economic Review, 104, 898–930. [2447,2449]
CANDOGAN,O . ,K .BIMPIKIS, AND A. OZDAGLAR (2012): “Optimal Pricing in Networks With Externalities,”
Operations Research, 60, 883–905. [2447]
CHUNG,F .R . ,AND F. C . GRAHAM (1997): Spectral Graph Theory, Vol. 92. American Mathematical Soc. [2452]
CVETKOVIC,D . ,D .M .C VETKOVI´C,P .R OWLINSON, AND S. S IMIC (1997): Eigenspaces of Graphs, Vol. 66.
Cambridge University Press. [2452]
DAVIES,E .B . ,G .M .G LADWELL,J .L EYDOLD, AND P. F. STADLER (2001): “Discrete Nodal Domain Theorems,” Linear Algebra and its Applications, 336, 51–60. [2452]
DEMANGE, G. (2017): “Optimal T argeting Strategies in a Network Under Complementarities,” Games and
Economic Behaviour, 105, 84–103. [2447]
DESAI,M . ,AND V. RAO (1994): “ A Characterization of the Smallest Eigenvalue of a Graph,”Journal of Graph
Theory, 18, 181–194. [2457]
FAINMESSER,I . , AND A. GALEOTTI (2017): “Pricing Network Effects,” Review of Economic Studies, 83, 165–
198. [2447]
GAITONDE,J . ,J .K LEINBERG, AND É. TARDOS (2020): “ Adversarial Perturbations of Opinion Dynamics in
Networks,” Report, Cornell University, https://arxiv.org/abs/2003.07010.[ 2464]
GALEOTTI,A . ,AND S. GOYAL(2009): “Inﬂuencing the Inﬂuencers: A Theory of Strategic Diffusion,”The Rand
Journal of Economics, 40, 509–532. [2447]
(2010): “The Law of the Few,” American Economic Review, 100, 1468–1492. [2450]
GALEOTTI,A . , AND B. W . ROGERS (2013): “Strategic Immunization and Group Structure,” American Economic Journal: Microeconomics, 5, 1–32. [2447]
GALEOTTI,A . ,B .G OLUB,S .G OYAL,E .T ALAMÀS, AND O. TAMUZ (2020): “T argeted T axes and Subsidies in
Supply Chains,” Report. [2464]
GALEOTTI,A . ,B .G OLUB S. GOYAL (2020): “Supplement to ‘T argeting Interventions in Networks’,” Econometrica Supplemental Material, 88, https://doi.org/10.3982/ECTA16173.[ 2448]
GALEOTTI,A . ,S .G OYAL,M .O .J ACKSON,F .V EGA-REDONDO, AND L. YARIV (2010): “Network Games,”
Review of Economic Studies , 77, 218–244. [2447]
GOLUB,B . ,AND M. O. JACKSON (2012): “How Homophily Affects the Speed of Learning and Best-Response
Dynamics,” The Quarterly Journal of Economics , 127, 1287–1338. [2459]
GOLUB,B . ,AND S. MORRIS (2020): “Expectations, Networks and Conventions,” Report, Department of Eonomics, Harvard University, https://arxiv.org/abs/2009.13802.[ 2460]
GOYAL,S . ,AND J. MORAGA-GONZALEZ (2001): “R&D Networks,” The Rand Journal of Economics, 32, 686–
707. [2446,2450]
GOYAL,S . ,J .M ORAGA, AND M. VAN DER LEIJ (2006): “Economics: An Emerging Small World?” Journal of
Political Economy, 114, 403–412. [2447]
HARTFIEL,D . , AND C. D. M EYER (1998): “On the Structure of Stochastic Matrices With a Subdominant
Eigenvalue Near 1,” Linear Algebra and its Applications, 272, 193–203. [2459]
JACKSON,M . ,B .W .ROGERS, AND Y. ZENOU (2017): “The Economic Consequences of Social-Network Structure,” Journal of Economic Literature , 55, 49–95. [2446]
KEMPE,D . ,J .KLEINBERG, AND E. TARDOS (2003): “Maximizing the Spread of Inﬂuence Through a Social Network,” in Proceedings 9th ACM SIGKDD International Conference on Knowledge Discovery and Data Mining .
[2447]


---


LAMBERT,N .S . ,G .M ARTINI, AND M. OSTROVSKY (2018): “Quadratic Games,” Working Paper No. 24914,
NBER. [2460]
LEDUC,M .V . ,M .O .J ACKSON, AND R. JOHARI (2017): “Pricing and Referrals in Diffusion on Networks,”
Games and Economic Behavior, 104, 568–594. [2447]
LEVIN,D .A . ,Y .PERES, AND E. L. WILMER (2009): Markov Chains and Mixing Times . Providence, RI: American Mathematical Society. [2459]
MORRIS,S . , AND H. S. S HIN (2002): “Social V alue of Public Information,” American Economic Review , 92,
1521–1534. [2446,2451]
ROGERS, E. (1983): Diffusion of Innovations (Third Ed.). New Y ork: Free Press. [2447]
SPIELMAN, D. A. (2007): “Spectral Graph Theory and Its Applications,” in 48th Annual IEEE Symposium on
Foundations of Computer Science (FOCS’07) . IEEE, 29–38. [2452]
URSCHEL, J. C. (2018): “Nodal Decompositions of Graphs,” Linear Algebra and its Applications, 539, 60–71.
[2452]
VALENTE, T . (2012): “Network Interventions,”Science, 337, 49–53. [2447]
Co-editor Dirk Bergemann handled this manuscript.
Manuscript received 12 March, 2018; ﬁnal version accepted 14 April, 2020; available online 23 April, 2020.
