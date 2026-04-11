```json
{
  "findings": [
    {
      "category": "abstract_positioning",
      "severity": "critical",
      "title": "Missing abstract",
      "snippet": "\\begin{document}\n\\maketitle\n\n\\section{Introduction}",
      "explanation": "The draft contains no \\begin{abstract}...\\end{abstract} block. Every general-academic venue—journals, conferences, workshops, and preprint servers—requires an abstract. Its absence signals the draft is not ready for any form of external review.",
      "fix": "Add a structured abstract (≈150–250 words) that states the problem, the proposed approach, the key result, and the main limitation.",
      "rewrite": "\\begin{abstract}\nWe study the graph optimization problem and propose a three-phase framework combining greedy partitioning, cluster merging, and local-search refinement. On five standard benchmarks the method achieves the best known objective on three, while remaining competitive on the other two. We analyze convergence properties and discuss current limitations.\n\\end{abstract}"
    },
    {
      "category": "introduction_positioning",
      "severity": "critical",
      "title": "Introduction lacks problem definition, motivation, and contribution list",
      "snippet": "Graphs are used in many applications.\nMany algorithms have been proposed.\nOur algorithm is better.\nWe test it on several datasets.",
      "explanation": "A general-academic audience expects the introduction to (a) define the specific problem, (b) motivate why it matters, (c) summarize limitations of existing work, and (d) enumerate concrete contributions. The current four-sentence introduction does none of these; 'Our algorithm is better' is an unsupported assertion that undermines credibility.",
      "fix": "Expand to ≥1 page: formalize the optimization objective, cite evidence of practical impact, contrast with prior art, and list numbered contributions (e.g., 'Our contributions are threefold: (1)…').",
      "rewrite": ""
    },
    {
      "category": "venue_alignment",
      "severity": "critical",
      "title": "Theorem stated but explicitly unproven",
      "snippet": "We do not prove this theorem formally but it seems intuitively obvious from the structure of the algorithm.",
      "explanation": "No academic venue accepts a labeled Theorem whose proof is replaced by 'it seems intuitively obvious.' This violates the basic contract of a theorem environment: a statement so labeled must be accompanied by a rigorous proof (or a precise citation to one). Presenting it this way will cause immediate rejection at any peer-reviewed venue.",
      "fix": "Either (a) supply a full proof or proof sketch with the key argument, (b) downgrade the statement to a Conjecture with supporting intuition, or (c) remove the theorem environment entirely and discuss convergence informally.",
      "rewrite": "\\begin{conjecture}\nThe proposed method converges to a local optimum in polynomial time.\n\\end{conjecture}\n\nWe offer informal evidence for this conjecture. Because each phase monotonically decreases the objective (Phase~1 by \\ldots, Phase~2 by \\ldots, Phase~3 by \\ldots), and the objective is lower-bounded, the sequence of iterates must converge. Bounding the number of improving steps by $O(n^k)$ would yield a polynomial-time guarantee; we leave a formal proof to future work."
    },
    {
      "category": "venue_alignment",
      "severity": "critical",
      "title": "Referenced table is missing",
      "snippet": "Table~1 shows the results but we were unable to include it due to space constraints.",
      "explanation": "Citing a table that does not exist in the manuscript is unacceptable at any venue. Empirical results are the primary evidence for the claims; omitting them removes the paper's evidentiary basis.",
      "fix": "Include Table 1 with full numerical results. If space is genuinely constrained, move supplementary tables to an appendix or supplementary material file, but the main results table must appear in the body.",
      "rewrite": ""
    },
    {
      "category": "venue_alignment",
      "severity": "major",
      "title": "Method phases presented out of logical order",
      "snippet": "In Phase 1, we compute a preliminary partition using a greedy approach.\nIn Phase 3, we refine the partition using local search.\nIn Phase 2, we merge small clusters.",
      "explanation": "Phases are presented in the order 1 → 3 → 2, which breaks the logical flow and confuses readers about the actual pipeline. A general-academic reader expects sequential exposition of an algorithm's stages.",
      "fix": "Reorder the paragraphs to Phase 1 → Phase 2 → Phase 3, matching the intended execution order.",
      "rewrite": "In Phase~1, we compute a preliminary partition using a greedy approach.\nIn Phase~2, we merge small clusters.\nIn Phase~3, we refine the partition using local search."
    },
    {
      "category": "venue_alignment",
      "severity": "major",
      "title": "Complexity claim contradicted by empirical evidence without reconciliation",
      "snippet": "The time complexity is $O(n \\log n)$ in the best case.\nHowever, in our experiments the runtime was often quadratic.",
      "explanation": "Stating a best-case complexity of O(n log n) and then reporting quadratic empirical behavior without analysis is a red flag. An academic reader will ask for worst-case and expected-case bounds, and an explanation of when and why the best case does not hold. The gap suggests the complexity analysis is incomplete or incorrect.",
      "fix": "Provide worst-case and average-case complexity. Explain the structural conditions under which the algorithm degrades to quadratic time, and relate those conditions to the experimental graphs.",
      "rewrite": ""
    },
    {
      "category": "audience_positioning",
      "severity": "major",
      "title": "Conclusion overclaims relative to reported results",
      "snippet": "We presented a novel framework for graph optimization that outperforms existing methods in most cases.",
      "explanation": "The experiments section reports winning on 3 of 5 datasets, with the other 2 favoring baselines. While 3/5 is technically 'most,' the conclusion glosses over the losses and does not qualify the claim. A general-academic audience expects honest, balanced summarization of results.",
      "fix": "Qualify the claim: specify the conditions or graph types where the method excels and where it does not, and avoid unqualified 'outperforms.'",
      "rewrite": "We presented a framework for graph optimization that matches or improves upon existing methods on three of five benchmarks, while underperforming on graphs with [specific property]. These mixed results suggest the approach is most effective for [characterization], and we outline directions to address the remaining gaps."
    },
    {
      "category": "audience_positioning",
      "severity": "major",
      "title": "Related work is superficial and does not position the contribution",
      "snippet": "Smith et al.\\ (2020) proposed a method for graph partitioning.\nJones et al.\\ (2021) extended this to weighted graphs.\nThere are also methods based on spectral clustering.",
      "explanation": "The related work lists three items without discussing their strengths, weaknesses, or relationship to the proposed method. A general-academic reader needs to understand what gap remains and why existing approaches are insufficient.",
      "fix": "For each cited line of work, state (a) what it achieves, (b) its key limitation, and (c) how the proposed framework addresses that limitation. Add coverage of other relevant families of methods.",
      "rewrite": ""
    },
    {
      "category": "venue_alignment",
      "severity": "major",
      "title": "Experiments dismiss negative results without investigation",
      "snippet": "We attribute this to the nature of the graphs, but we did not investigate further.",
      "explanation": "Explicitly stating that a negative result was not investigated is a significant weakness for any academic venue. Reviewers expect at minimum a hypothesis, a preliminary analysis (e.g., graph density, degree distribution), or a discussion of what further experiments would clarify.",
      "fix": "Offer a concrete hypothesis (e.g., 'We conjecture the greedy Phase 1 yields poor initial partitions on highly irregular degree distributions') and, ideally, a small ablation or diagnostic experiment to support it.",
      "rewrite": ""
    },
    {
      "category": "audience_positioning",
      "severity": "minor",
      "title": "Circular justification in conclusion",
      "snippet": "Our contribution is significant because graph optimization is important.",
      "explanation": "This sentence is a tautology that adds no information. A general-academic reader expects significance to be argued in terms of concrete improvements, new theoretical insights, or practical impact—not by restating that the problem domain is important.",
      "fix": "Replace with a specific significance statement, e.g., 'Our framework reduces partitioning time by X% on large social-network graphs, enabling real-time community detection in streaming settings.'",
      "rewrite": ""
    }
  ]
}
```
