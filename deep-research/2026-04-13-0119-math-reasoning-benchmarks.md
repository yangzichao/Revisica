# Survey of Benchmarks for Mathematical Reasoning and Proof Verification in Academic Papers

## Executive Summary

There are 25+ publicly available benchmarks relevant to evaluating mathematical reasoning and proof verification, but **critical gaps exist** for 3 of the 10 target dimensions: assumption auditing, definition completeness, and notation consistency have **no dedicated benchmarks**. The strongest coverage exists for multi-step reasoning error detection (5+ benchmarks with step-level annotations) and algebraic/computation verification. For paper-level review, three new benchmarks (SPOT, FLAWS, PaperAudit-Bench) emerged in 2025-2026 and are the most directly relevant to Revisica's use case, but model performance on them is extremely low (best: 21% recall on SPOT). The highest-priority integration candidates are **PRMBench** (richest error taxonomy, Apache-2.0, HuggingFace), **ASyMOB** (symbolic verification, HuggingFace), and **SPOT/FLAWS** (paper-level error detection, pending availability confirmation).

---

## Key Findings by Dimension

### Dimension 1: Proof-Statement Consistency

**Does the proof actually prove what the theorem claims?**

| Benchmark | What It Tests | Size | Format | Availability |
|-----------|--------------|------|--------|-------------|
| **FormalAlign** (ICLR 2025) | Automated alignment evaluation between informal and formal statements | Evaluated on MiniF2F + FormL4 subsets | Trains alignment model, scores formal-informal pairs | [GitHub](https://github.com/rookie-joe/FormalAlign) |
| **Con-NF** (ICLR 2025) | Research-level autoformalization alignment from New Foundations | 961 informal-formal statement pairs | Lean 4 formal statements paired with informal | Available via paper |
| **FormalMATH** | Formal verification of mathematical statements in Lean 4 | 5,560 formally verified statements | Lean 4 statements | [spherelab.ai/FormalMATH](https://spherelab.ai/FormalMATH/) |

**Assessment**: Partial coverage. FormalAlign measures whether a formalization faithfully captures the informal statement, which is the closest analog to proof-statement consistency. However, these benchmarks operate in the formal (Lean/Isabelle) domain. **No benchmark tests proof-statement consistency in natural-language mathematical papers.**

---

### Dimension 2: Assumption Auditing

**Are assumptions sufficient? Hidden assumptions?**

| Benchmark | Relevance | Notes |
|-----------|----------|-------|
| **PRMBench** | Partial | Tests "Prerequisite Sensitivity" (PS) as one of 9 error categories |
| **SPOT** | Incidental | Some errata/retractions involve assumption errors |

**Assessment**: **GAP.** No benchmark specifically evaluates whether a proof uses hidden assumptions, whether stated assumptions are sufficient, or whether assumptions are properly disclosed. PRMBench's "Prerequisite Sensitivity" dimension is the closest, testing whether PRMs detect when prerequisites are missing from reasoning steps, but this is at the step level, not the proof/theorem level.

---

### Dimension 3: Definition Completeness

**Undefined terms, vague definitions?**

| Benchmark | Relevance | Notes |
|-----------|----------|-------|
| None dedicated | -- | -- |

**Assessment**: **GAP.** No benchmark exists for this dimension. The autoformalization literature (IndiMathBench, FormalMATH) encounters undefined-term issues as a *failure mode* of formalization, not as an evaluation target. When LLMs fail to autoformalize, "definition misalignment between informal mathematics and formal libraries" is identified as the major cause, but no one has built a benchmark around detecting this in papers.

---

### Dimension 4: Generic Algebraic Verification

**Checking algebraic identities, equation solving?**

| Benchmark | What It Tests | Size | Format | Availability |
|-----------|--------------|------|--------|-------------|
| **ASyMOB** | Core symbolic manipulation (algebra, calculus, polynomials) | 17,092 challenges | Text problems with SymPy-verified answers | [HuggingFace](https://huggingface.co/datasets/Shalyt/ASyMOB-Algebraic_Symbolic_Mathematical_Operations_Benchmark), [GitHub](https://github.com/RamanujanMachine/ASyMOB) |
| **DeepMind Math Dataset** | School-level algebra, arithmetic, calculus, polynomials | 2M Q/A pairs per module | Text question -> text answer | [HuggingFace](https://huggingface.co/datasets/deepmind/math_dataset), [GitHub](https://github.com/google-deepmind/mathematics_dataset) |
| **SciBench** | College-level scientific problems (includes math) | 869 problems | Open-ended free-response requiring multi-step reasoning | [GitHub](https://github.com/mandyyyyii/scibench) |
| **MathBench** | Hierarchical math from arithmetic to college level | 3,709 questions | Theory + application questions by education stage | [GitHub](https://github.com/open-compass/MathBench) |

**Assessment**: Well covered for *solving* algebraic problems. Less coverage for *verifying* algebraic steps in existing proofs or papers. ASyMOB with SymPy-based verification is the most directly relevant for Revisica's algebraic checking pipeline.

---

### Dimension 5: Algorithm Correctness

**Pseudocode bugs, loop invariants?**

| Benchmark | What It Tests | Size | Format | Availability |
|-----------|--------------|------|--------|-------------|
| **CLEVER** | End-to-end verified code generation in Lean | 161 problems | Specification + Lean implementation + proof | [Paper](https://arxiv.org/abs/2505.13938) |
| **VerifyThisBench** | Formal methods competition: spec, implementation, verification | Competition-style problems | Code + formal spec + proof | [Paper](https://arxiv.org/abs/2505.19271) |
| **VeriBench** | End-to-end formal code verification in Lean 4 | Not specified | Python functions + Lean 4 formalizations + correctness proofs | [OpenReview](https://openreview.net/forum?id=rWkGFmnSNl) |

**Assessment**: Partial coverage. These benchmarks test *generating* correct code with formal verification, not *detecting bugs in pseudocode presented in academic papers*. The gap between "generate verified code" and "find bugs in paper pseudocode" is significant. **No benchmark specifically tests pseudocode bug detection in academic papers.**

---

### Dimension 6: Citation/Reference Accuracy

**Do citations support the claims made?**

| Benchmark | What It Tests | Size | Format | Availability |
|-----------|--------------|------|--------|-------------|
| **DeepResearch Bench** | Citation count and accuracy in research tasks | 100 PhD-level tasks across 22 fields | Research queries -> evaluated reports with citations | [Paper](https://deepresearch-bench.github.io/) |
| **ClimateViz** | Scientific fact-checking against charts | 49,862 claims + 2,896 visualizations | Claims labeled support/refute/insufficient info | [Paper](https://arxiv.org/abs/2506.08700) |
| **SPOT** | Paper-level error detection (includes citation errors) | 83 papers, 91 errors | Full papers -> error identification | [arXiv](https://arxiv.org/abs/2505.11855) |

**Assessment**: Partial coverage. DeepResearch Bench evaluates whether AI generates accurate citations, but does not evaluate whether *existing* citations in a paper correctly support their claims. **No benchmark specifically tests "does cited reference X actually support claim Y" in math papers.**

---

### Dimension 7: Notation Consistency

**Symbol usage consistency across a paper?**

| Benchmark | Relevance | Notes |
|-----------|----------|-------|
| None | -- | -- |

**Assessment**: **GAP.** No benchmark exists for notation consistency checking. This is an entirely unaddressed dimension in the literature. Notation inconsistency (e.g., using `x` for two different variables, switching between `f(x)` and `F(x)` without explanation) is a common paper-quality issue but no one has built a dataset around it.

---

### Dimension 8: Logical Reasoning Gaps

**Inference soundness, circular logic?**

| Benchmark | What It Tests | Size | Format | Availability |
|-----------|--------------|------|--------|-------------|
| **PRMBench** | 9 error categories including Non-Circular Logic (NCL), Empirical Soundness (ES), Step Consistency (SC), Deception Resistance (DR) | 6,216 problems, 83,456 step-level labels | JSON with original/modified solutions + error annotations | [HuggingFace](https://huggingface.co/datasets/hitsmy/PRMBench_Preview), [GitHub](https://github.com/ssmisya/PRMBench), Apache-2.0 |
| **Socratic-PRMBench** | 6 reasoning patterns: Transformation, Decomposition, Regather, Deduction, Verification, Integration | Not specified | Step-level reasoning pattern evaluation | [arXiv](https://arxiv.org/abs/2505.23474) |
| **ProcessBench** | Step-by-step error identification | 3,400 test cases | Math solutions with step-level error labels | Already integrated |
| **FineLogic** | Fine-grained logical reasoning | Not specified | Multiple logical reasoning subtasks | ACL 2025 |
| **LogicAsker** | Logical reasoning evaluation | Not specified | Evaluation framework | EMNLP 2024 |

**Assessment**: Well covered at the step level. PRMBench is the richest resource with its 9-category error taxonomy. Circular logic detection is explicitly tested (NCL category). However, coverage is at the *reasoning step* level, not at the *paper structure* level (e.g., detecting when a theorem's proof implicitly uses the theorem itself).

---

### Dimension 9: Computation Verification

**Checking numerical/symbolic computations?**

| Benchmark | What It Tests | Size | Format | Availability |
|-----------|--------------|------|--------|-------------|
| **ORCA** | Real-world calculation accuracy across domains | 500 tasks | Natural language -> deterministic calculator-verified outputs | [arXiv](https://arxiv.org/abs/2511.02589), [omnicalculator.com](https://www.omnicalculator.com/reports/omni-research-on-calculation-in-ai-benchmark) |
| **ASyMOB** | Symbolic manipulation (algebra, calculus) | 17,092 challenges | SymPy-verified answers | [HuggingFace](https://huggingface.co/datasets/Shalyt/ASyMOB-Algebraic_Symbolic_Mathematical_Operations_Benchmark) |
| **DeepMind Math Dataset** | Procedural math computation | 2M+ Q/A pairs | Generated question -> answer pairs | [HuggingFace](https://huggingface.co/datasets/deepmind/math_dataset) |

**Assessment**: Covered. ORCA is particularly notable for showing that frontier models only achieve 45-63% accuracy on real-world calculations, with 68% of errors being mechanical (calculation errors + rounding issues). ASyMOB provides SymPy-verified algebraic challenges.

---

### Dimension 10: Multi-Step Mathematical Reasoning

**Error detection in long derivations?**

| Benchmark | What It Tests | Size | Format | Availability |
|-----------|--------------|------|--------|-------------|
| **ProcessBench** | Step-by-step error identification in math reasoning | 3,400 test cases | Competition/Olympiad solutions with error labels | Already integrated |
| **PRMBench** | Fine-grained process-level error detection | 6,216 problems, 83,456 step labels | JSON with step-level error annotations | [HuggingFace](https://huggingface.co/datasets/hitsmy/PRMBench_Preview), Apache-2.0 |
| **MPBench** | Multimodal process-level error identification | 9,745 instances | Three evaluation paradigms | [arXiv](https://arxiv.org/abs/2503.12505) |
| **Socratic-PRMBench** | Reasoning pattern evaluation | Not specified | Step-level pattern evaluation | [arXiv](https://arxiv.org/abs/2505.23474) |
| **MATH-500** | Competition-level multi-step problems | 500 problems | LaTeX problems -> solutions | [HuggingFace](https://huggingface.co/datasets/hendrycks/competition_math) |
| **HARP** | US competition math, 6 difficulty levels | 5,409 problems | Problems with auto-checkable answers + human solutions | [GitHub](https://github.com/aadityasingh/HARP) |

**Assessment**: Best-covered dimension. Multiple benchmarks with step-level annotations. PRMBench is the richest single resource for this dimension.

---

## Paper-Level Review Benchmarks (Cross-Cutting)

These benchmarks are the most directly relevant to Revisica's core use case of reviewing academic papers.

| Benchmark | What It Tests | Size | Input/Output | Best Model Performance | Availability |
|-----------|--------------|------|-------------|----------------------|-------------|
| **SPOT** | Error detection in published papers (errata/retractions) | 83 papers, 91 errors | Full papers -> error identification (recall/precision) | o3: 21.1% recall, 6.1% precision | [arXiv](https://arxiv.org/abs/2505.11855), dataset availability TBD |
| **FLAWS** | Error identification and localization in scientific papers | 713 paper-error pairs | Papers with errors -> ranked error candidates | GPT 5: 39.1% at k=10 | [arXiv](https://arxiv.org/abs/2511.21843), dataset availability TBD |
| **PaperAudit-Bench** | Error detection + evidence-aware review generation | Not specified | Papers -> error detection + review generation | Not reported in abstract | [arXiv](https://arxiv.org/abs/2601.19916) (Jan 2026) |
| **IMProofBench** | Research-level proof generation quality | 39 problems | Agentic framework with tools -> full proofs | GPT-5: 22% fully correct | [improofbench.math.ethz.ch](https://improofbench.math.ethz.ch/) |
| **FormalProofBench** | Graduate-level formal theorem proving | 200 problems | Natural language + formal statement -> Lean proof | Best: 33.5% accuracy | [arXiv](https://arxiv.org/abs/2603.26996) |

---

## Formal Proof Verification Benchmarks (Reference)

| Benchmark | Size | Format | Availability |
|-----------|------|--------|-------------|
| **MiniF2F** (OpenAI) | 488 problems | Lean/Metamath/Isabelle | [HuggingFace](https://huggingface.co/datasets/AI-MO/minif2f_test), [GitHub](https://github.com/openai/miniF2F) |
| **PutnamBench** | 1,724 formalizations | Lean 4/Isabelle/Coq | [GitHub](https://github.com/trishullab/PutnamBench), Apache-2.0/MIT |
| **FormalMATH** | 5,560 statements | Lean 4 | [spherelab.ai/FormalMATH](https://spherelab.ai/FormalMATH/) |
| **FormalProofBench** | 200 problems | Lean 4 | [arXiv](https://arxiv.org/abs/2603.26996) |
| **MathConstruct** | 127 problems | Constructive proofs, auto-verified | [GitHub](https://github.com/eth-sri/mathconstruct) |

---

## Competition/Reasoning Benchmarks (Reference)

| Benchmark | Size | Status | Availability |
|-----------|------|--------|-------------|
| **MATH-500** | 500 | Near-saturated (96%) | [HuggingFace](https://huggingface.co/datasets/hendrycks/competition_math) |
| **GSM8K** | 8,500 | Saturated (>97%) | HuggingFace |
| **HARP** | 5,409 | Active (hardest: 41% for o1-mini) | [GitHub](https://github.com/aadityasingh/HARP) |
| **OmniMath** | 4,428 | Active | [GitHub](https://github.com/KbsdJames/Omni-MATH) |
| **FrontierMath** | 350 | Active, mostly private | Contact Epoch AI |
| **RealMath** | 1,286 | Active, continuously refreshed | [GitHub](https://github.com/ethz-spylab/RealMath) |
| **AIME 2024/2025** | ~30/year | Active | Public problems |

---

## Gap Analysis Summary

| # | Dimension | Coverage Level | Best Available Benchmark | Critical Gap? |
|---|-----------|---------------|------------------------|--------------|
| 1 | Proof-statement consistency | Partial (formal only) | FormalAlign | YES -- no natural-language benchmark |
| 2 | Assumption auditing | Minimal | PRMBench (PS category) | YES -- no dedicated benchmark |
| 3 | Definition completeness | None | None | YES -- complete gap |
| 4 | Algebraic verification | Good (problem-solving) | ASyMOB | No -- but gap for *checking* existing proofs |
| 5 | Algorithm correctness | Partial (code, not pseudocode) | CLEVER, VerifyThisBench | Moderate -- no pseudocode-in-papers benchmark |
| 6 | Citation accuracy | Partial | DeepResearch Bench | Moderate -- no claim-citation alignment benchmark |
| 7 | Notation consistency | None | None | YES -- complete gap |
| 8 | Logical reasoning gaps | Good (step-level) | PRMBench | No -- though paper-level coverage is thin |
| 9 | Computation verification | Good | ORCA, ASyMOB | No |
| 10 | Multi-step reasoning | Excellent | PRMBench, ProcessBench | No |

**Three complete gaps**: Assumption auditing (#2), Definition completeness (#3), Notation consistency (#7).

**Three partial gaps**: Proof-statement consistency in natural language (#1), Algorithm correctness for pseudocode (#5), Citation-claim alignment (#6).

---

## Integration Recommendations for Revisica

### Priority 1: Integrate Now

| Benchmark | Why | Effort |
|-----------|-----|--------|
| **PRMBench** | Richest error taxonomy (9 categories), 83K step labels, Apache-2.0, HuggingFace ready | Medium -- JSON format, need to map to Revisica eval framework |
| **ASyMOB** | Directly relevant to algebraic verification pipeline, SymPy-based, HuggingFace ready | Low -- SymPy verification aligns with existing math_check infrastructure |

### Priority 2: Integrate When Available

| Benchmark | Why | Blocker |
|-----------|-----|---------|
| **SPOT** | Most relevant paper-level benchmark, tests real errata/retractions | Dataset availability unclear -- may need to contact authors |
| **FLAWS** | 713 paper-error pairs, complementary to SPOT | Dataset availability unclear |
| **ORCA** | Computation verification, reveals frontier model weaknesses | Need to verify dataset access |

### Priority 3: Build Internally

| Dimension | Why Build? | Approach |
|-----------|-----------|----------|
| **Notation consistency** | Complete gap, highly relevant to paper review | Synthesize from LaTeX papers: inject notation inconsistencies, label them |
| **Assumption auditing** | Complete gap, core to proof review | Extract theorems+proofs from papers, inject hidden assumption errors |
| **Definition completeness** | Complete gap, relevant to paper quality | Remove/obscure definitions from papers, test detection |

---

## Open Risks & Unknowns

1. **SPOT and FLAWS dataset availability**: Both are described in papers but neither has a confirmed public dataset release. SPOT was published May 2025 and FLAWS November 2025; both may still be in the process of releasing data.

2. **Paper-level vs. step-level gap**: Most existing benchmarks operate at the reasoning-step level (individual equations, solution steps). Revisica's use case requires paper-level evaluation (cross-section reasoning, structural consistency). This gap is partially addressed by SPOT/FLAWS/PaperAudit-Bench but their availability is uncertain.

3. **Formal vs. informal gap**: Many proof verification benchmarks (MiniF2F, PutnamBench, FormalMATH) require Lean/Isabelle/Coq formalization. Revisica works with natural-language LaTeX papers. The translation gap between formal and informal verification is significant and not well-benchmarked.

4. **Frontier model performance on paper review is very low**: SPOT's best result is 21% recall at 6% precision. FLAWS's best is 39% at k=10. This suggests that even with good benchmarks, the task of automated paper review remains extremely challenging for current models.

---

## Assumptions

- "Publicly available" means the dataset can be downloaded without payment, though some may require agreeing to terms or contacting authors.
- Benchmark sizes and performance numbers are taken from papers as of their publication date; some may have been updated since.
- The 10 dimensions are treated as independent, though in practice they overlap (e.g., logical reasoning gaps can involve hidden assumptions).

---

## Sources

- [PRMBench](https://github.com/ssmisya/PRMBench) -- ACL 2025, fine-grained PRM evaluation, Apache-2.0
- [PRMBench HuggingFace](https://huggingface.co/datasets/hitsmy/PRMBench_Preview) -- dataset preview
- [ASyMOB](https://huggingface.co/datasets/Shalyt/ASyMOB-Algebraic_Symbolic_Mathematical_Operations_Benchmark) -- algebraic symbolic benchmark
- [SPOT](https://arxiv.org/abs/2505.11855) -- paper-level error detection benchmark
- [FLAWS](https://arxiv.org/abs/2511.21843) -- error identification in scientific papers
- [PaperAudit-Bench](https://arxiv.org/abs/2601.19916) -- error detection in research papers
- [FormalAlign](https://github.com/rookie-joe/FormalAlign) -- ICLR 2025, autoformalization alignment
- [MiniF2F](https://github.com/openai/miniF2F) -- cross-system formal math benchmark
- [PutnamBench](https://github.com/trishullab/PutnamBench) -- undergraduate competition formal proofs
- [FormalMATH](https://spherelab.ai/FormalMATH/) -- 5,560 formal statements in Lean 4
- [FormalProofBench](https://arxiv.org/abs/2603.26996) -- graduate-level formal proofs
- [IMProofBench](https://improofbench.math.ethz.ch/) -- research-level proof generation
- [HARP](https://github.com/aadityasingh/HARP) -- US competition math, 5,409 problems
- [OmniMath](https://github.com/KbsdJames/Omni-MATH) -- 4,428 Olympiad-level problems
- [FrontierMath](https://epoch.ai/benchmarks/frontiermath) -- research-level math, mostly private
- [MathConstruct](https://github.com/eth-sri/mathconstruct) -- constructive proof benchmark
- [RealMath](https://github.com/ethz-spylab/RealMath) -- continuously refreshed research math
- [DeepMind Math Dataset](https://huggingface.co/datasets/deepmind/math_dataset) -- procedural math generation
- [ORCA Benchmark](https://arxiv.org/abs/2511.02589) -- real-world calculation accuracy
- [SciBench](https://github.com/mandyyyyii/scibench) -- college-level scientific problem solving
- [MathBench](https://github.com/open-compass/MathBench) -- hierarchical math benchmark
- [MPBench](https://arxiv.org/abs/2503.12505) -- multimodal process-level benchmark
- [Socratic-PRMBench](https://arxiv.org/abs/2505.23474) -- reasoning pattern evaluation
- [MATH-500 / Hendrycks MATH](https://huggingface.co/datasets/hendrycks/competition_math) -- competition math
- [DeepResearch Bench](https://deepresearch-bench.github.io/) -- citation accuracy evaluation
- [ClimateViz](https://arxiv.org/abs/2506.08700) -- scientific fact-checking on charts
- [Survey of Mathematical Reasoning](https://arxiv.org/abs/2412.11936) -- comprehensive survey (2024)
- [CLEVER](https://arxiv.org/abs/2505.13938) -- verified code generation in Lean
- [VerifyThisBench](https://arxiv.org/abs/2505.19271) -- formal verification competition
