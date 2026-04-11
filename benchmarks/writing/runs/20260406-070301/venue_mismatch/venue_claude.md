```json
{
  "findings": [
    {
      "category": "venue_alignment",
      "severity": "critical",
      "title": "Advocacy tone incompatible with scientific register",
      "snippet": "Why Minimum Wage Laws Are Bad: A Super Quick Math Proof",
      "explanation": "Top-5 economics journals (AER, QJE, JPE, Econometrica, ReStud) require neutral, descriptive titles that signal a precise research contribution. This title reads as an opinion-editorial headline: it pre-announces a normative conclusion ('Are Bad') and uses colloquial language ('Super Quick'). No top-5 paper frames its contribution as proving a policy is 'bad'; they characterize effects, magnitudes, and mechanisms.",
      "fix": "Replace with a neutral, contribution-specific title that describes the economic mechanism or empirical finding.",
      "rewrite": "Employment Effects of Binding Wage Floors in Competitive Labor Markets: A Theoretical Reassessment"
    },
    {
      "category": "abstract_positioning",
      "severity": "critical",
      "title": "Abstract lacks every element expected by top-5 journals",
      "snippet": "So basically everyone knows that minimum wage laws mess up the labor market. In this paper I'm going to show you a really cool model that proves it. My model is way better than what other people have done before. Trust me, the math checks out.",
      "explanation": "A top-5 abstract must contain: (1) a crisp statement of the research question or puzzle, (2) a brief description of methodology/data, (3) the main quantitative or qualitative result, and (4) the economic or policy implication. This abstract contains none of these. 'So basically,' 'really cool,' 'Trust me' are categorically inappropriate registers. The claim 'way better than what other people have done' is unsubstantiated and dismissive of prior literature—a disqualifying signal for referees.",
      "fix": "Rewrite the abstract in formal academic prose: state the question, describe the model's novel feature, report the main result precisely, and note implications with appropriate hedging.",
      "rewrite": "This paper examines the employment consequences of minimum wage legislation in a competitive labor market framework. We characterize the equilibrium in a linear supply-and-demand model and derive conditions under which a binding wage floor generates excess labor supply. Our results complement the existing literature by [state novel contribution]. The analysis suggests that the magnitude of disemployment effects depends critically on the elasticities of labor supply and demand."
    },
    {
      "category": "introduction_positioning",
      "severity": "critical",
      "title": "Introduction lacks literature engagement, contribution statement, and identification of a gap",
      "snippet": "A bunch of economists have argued about it forever. Some people think it's good, some think it's bad. I personally think the evidence clearly shows it's bad, and I'll prove it here.",
      "explanation": "Top-5 introductions follow a well-known structure: (1) motivate with a specific economic question or puzzle, (2) summarize what the literature has established, (3) identify a precise gap or unresolved tension, (4) state the paper's contribution, (5) preview key results with specifics. This introduction provides none of these. 'A bunch of economists' is not a literature review. 'I personally think' signals subjective advocacy, not scientific inquiry. Top-5 referees expect engagement with Card and Krueger (1994), Neumark and Wascher (2008), Dube, Lester, and Reich (2010), Cengiz et al. (2019), and many others—not dismissal.",
      "fix": "Restructure the introduction to open with a motivating fact or policy question, provide a focused literature review situating the contribution, and state the paper's value-added in precise terms.",
      "rewrite": null
    },
    {
      "category": "venue_alignment",
      "severity": "critical",
      "title": "Model contributes no novelty beyond textbook competitive equilibrium",
      "snippet": "Consider a labor market with supply $S(w) = aw$ and demand $D(w) = b - cw$ ... which means there's unemployment. QED.",
      "explanation": "This is a first-year undergraduate supply-and-demand exercise. Top-5 journals require a model that either (a) introduces a novel mechanism, (b) generates non-obvious comparative statics, (c) resolves an existing theoretical puzzle, or (d) provides a structural framework for empirical estimation. The result that a binding price floor creates excess supply is the definition of a price floor; labeling it 'QED' does not constitute a contribution. Econometrica and ReStud, in particular, demand substantial theoretical innovation.",
      "fix": "Develop a model with features that generate new insights—e.g., monopsony power, search frictions, worker heterogeneity, firm entry/exit, or general equilibrium effects—and derive results that are not immediate from textbook definitions.",
      "rewrite": null
    },
    {
      "category": "venue_alignment",
      "severity": "critical",
      "title": "Empirical section contains no actual empirical analysis",
      "snippet": "I looked at some data from the internet and it seems to confirm my model. Figure~1 shows the relationship but I couldn't get the plotting software to work so you'll have to take my word for it.",
      "explanation": "Top-5 journals require rigorous empirical methodology: clearly specified data sources, identification strategies (difference-in-differences, regression discontinuity, instrumental variables, etc.), robustness checks, and transparent reporting. 'Data from the internet' is not a data description. A missing figure with 'take my word for it' is unpublishable at any peer-reviewed venue. This section would result in immediate desk rejection.",
      "fix": "Either remove the empirical section entirely and frame the paper as purely theoretical, or conduct a full empirical analysis with identified data sources, a credible research design, standard errors, and all figures/tables included.",
      "rewrite": null
    },
    {
      "category": "audience_positioning",
      "severity": "critical",
      "title": "Dismissal of canonical literature without substantive critique",
      "snippet": "Also Card and Krueger (1994) found the opposite but their methodology is super flawed in my opinion.",
      "explanation": "Card and Krueger (1994) is among the most influential papers in labor economics and appeared in the AER. Dismissing it as 'super flawed in my opinion' without specifying the methodological concern, providing an alternative estimate, or engaging with the subsequent debate (Neumark and Wascher 2000; Dube et al. 2010) signals unfamiliarity with the field. Top-5 referees will view this as a disqualifying lack of scholarly engagement.",
      "fix": "If critiquing Card and Krueger, specify the exact methodological concern (e.g., choice of control group, parallel trends assumption, measurement error), cite the relevant replication studies, and demonstrate empirically or formally why the concern matters for their conclusions.",
      "rewrite": "Card and Krueger (1994) find no significant disemployment effects using a difference-in-differences design around New Jersey's 1992 minimum wage increase. Neumark and Wascher (2000) challenge these findings using payroll data rather than survey data, obtaining negative employment effects. Our framework provides conditions under which these divergent findings can be reconciled: specifically, when [state mechanism]."
    },
    {
      "category": "venue_alignment",
      "severity": "major",
      "title": "Conclusion contains self-assessment and ad hominem framing",
      "snippet": "Policymakers should listen to economists like me instead of pushing ideological agendas. This paper is definitely publishable in a top economics journal.",
      "explanation": "Top-5 conclusions summarize contributions, acknowledge limitations, and suggest avenues for future research. Self-declaring publishability and accusing policymakers of 'ideological agendas' is unprofessional and would alienate any referee. Even strong policy conclusions in top-5 papers are stated with appropriate hedging and caveats.",
      "fix": "Replace with a professional summary of contributions, a discussion of caveats and limitations, and directions for future work.",
      "rewrite": "This paper has characterized the employment consequences of minimum wage legislation in a competitive labor market with linear supply and demand. Several limitations merit emphasis: the model abstracts from monopsony power, search frictions, and general equilibrium effects, each of which may attenuate or reverse the baseline prediction. Future work should incorporate these features and bring the model to data using quasi-experimental variation in minimum wage policies."
    },
    {
      "category": "venue_alignment",
      "severity": "major",
      "title": "Pervasive informal register throughout the paper",
      "snippet": "OK so here's my model.",
      "explanation": "Top-5 economics papers maintain formal academic prose throughout. Phrases like 'OK so,' 'really elegant,' 'demolishes,' 'hot topic,' 'a bunch of,' and 'wraps things up' are characteristic of blog posts or undergraduate writing, not scholarly publications. This register mismatch would trigger desk rejection before any evaluation of content.",
      "fix": "Revise the entire manuscript into formal academic English. Use 'We' rather than 'I,' avoid colloquialisms, and adopt the restrained, precise tone characteristic of the target venues.",
      "rewrite": null
    },
    {
      "category": "venue_alignment",
      "severity": "major",
      "title": "No reference list or proper citations",
      "snippet": "Also Card and Krueger (1994) found the opposite but their methodology is super flawed in my opinion.",
      "explanation": "The paper mentions Card and Krueger (1994) in passing but includes no bibliography, no \\bibliography command, and no BibTeX file. Top-5 journals require comprehensive, properly formatted reference lists. More fundamentally, this paper cites essentially zero literature, whereas a top-5 minimum wage paper would need to engage with dozens of references.",
      "fix": "Add a complete bibliography using BibTeX or \\thebibliography, citing all relevant theoretical and empirical work on minimum wages.",
      "rewrite": null
    }
  ]
}
```
