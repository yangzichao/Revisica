# ReviseAgent

ReviseAgent is a minimal POC for reviewing LaTeX-first academic drafts with Codex and Claude.

Current scope:

- Focus on `.tex` files first.
- Support a deterministic `math-review` lane for symbolic math checks.
- Detect whether `codex` and `claude` CLIs are installed.
- Auto-install local review assets when they are missing.
- Run one or both providers against the same LaTeX draft.
- Always try to produce one user-facing `final_report.md`.

This POC assumes "Cloud" in the original idea means `Claude`.

## What the POC does

1. `bootstrap`
   - Detects `codex` and `claude`.
   - Installs a local `revise-agent` plugin and `latex-paper-review` skill for each platform.
   - Installs a lightweight local agent profile used by the Python runner.
2. `review` (unified)
   - Runs writing-review and math-review concurrently as independent lanes.
   - Each lane produces its own report in a subdirectory (`writing/`, `math/`).
   - A top-level `summary.md` links both lane outputs.
   - Accepts options for both lanes (venue profile, LLM proof review, etc.).
3. `math-review`
   - Extracts simple mathematical claims from the LaTeX source.
   - Uses SymPy to check definite integrals and average-value claims.
   - Uses symbolic continuity-domain checks to catch obvious bad continuity claims.
   - Extracts theorem/proof environments into a lightweight `blueprint-lite` structure.
   - Breaks proofs into proof obligations so later LLM or human review can inspect specific steps.
   - Can optionally ask Codex and/or Claude to review those proof obligations and flag suspicious steps.
   - When multiple providers review the same proof obligations, ReviseAgent adjudicates them into a cleaner merged math conclusion.
   - Produces a machine-focused math report, with or without provider assistance.
4. `writing-review`
   - Runs specialized writing agents for baseline language hygiene, structure/logic, and venue/style alignment.
   - Defaults to cross-check when multiple providers are installed.
   - Supports venue profiles such as `general-academic` and `econ-top5`.
   - Produces one writing-focused `final_report.md` after a judge/adjudicator merges role outputs.

## Quick Start

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install .
revise-agent bootstrap
revise-agent math-review examples/minimal_paper.tex
revise-agent math-review examples/proof_blueprint_demo.tex --llm-proof-review --targets codex
revise-agent writing-review examples/minimal_paper.tex
revise-agent writing-review examples/minimal_paper.tex --venue-profile econ-top5 --reviewer-a codex:gpt-5.4 --reviewer-b claude:sonnet
revise-agent review examples/minimal_paper.tex
revise-agent review examples/minimal_paper.tex --venue-profile econ-top5 --llm-proof-review
revise-agent benchmark-math
revise-agent benchmark-writing
revise-agent import-proofnet --split test --limit 5
revise-agent benchmark-proofnet --split test --limit 5
revise-agent benchmark-proofnet --split test --limit 3 --llm-proof-review --targets codex claude
revise-agent benchmark-run --suite math-cases --mode deterministic-only
revise-agent benchmark-run --suite proofnet --mode single-agent-self-check --limit 1 --reviewer codex:gpt-5.4 --self-checker codex:gpt-5.4-mini
revise-agent benchmark-run --suite proofnet --mode multi-agent-cross-check --limit 1 --reviewer-a codex:gpt-5.4 --reviewer-b claude:sonnet
revise-agent benchmark-run --suite proofbench --mode deterministic-only --limit 5
revise-agent benchmark-run --suite processbench --mode deterministic-only --split math --limit 5
```

## CLI

```bash
revise-agent bootstrap
revise-agent bootstrap --targets codex
revise-agent review path/to/paper.tex
revise-agent review path/to/paper.tex --venue-profile econ-top5
revise-agent review path/to/paper.tex --llm-proof-review --targets codex claude
revise-agent review path/to/paper.tex --reviewer-a codex:gpt-5.4 --reviewer-b claude:sonnet --judge codex:gpt-5.4
revise-agent writing-review path/to/paper.tex
revise-agent writing-review path/to/paper.tex --venue-profile econ-top5
revise-agent writing-review path/to/paper.tex --reviewer-a codex:gpt-5.4 --reviewer-b claude:sonnet --judge codex:gpt-5.4
revise-agent math-review path/to/paper.tex
revise-agent math-review path/to/paper.tex --llm-proof-review --targets codex claude
revise-agent benchmark-math
revise-agent benchmark-writing
revise-agent benchmark-writing --venue-profile econ-top5 --timeout-seconds 180
revise-agent import-proofnet --split test --limit 10
revise-agent benchmark-proofnet --split test --limit 10
revise-agent benchmark-proofnet --split test --limit 3 --llm-proof-review --targets codex claude
revise-agent benchmark-run --suite math-cases --mode deterministic-only
revise-agent benchmark-run --suite proofnet --mode single-agent
revise-agent benchmark-run --suite proofnet --mode single-agent-self-check --reviewer codex:gpt-5.4 --self-checker codex:gpt-5.4-mini
revise-agent benchmark-run --suite proofnet --mode multi-agent-cross-check --reviewer-a codex:gpt-5.4 --reviewer-b claude:sonnet
revise-agent benchmark-run --suite proofnet --mode hybrid-cross --reviewer-a codex:gpt-5.4 --reviewer-b claude:sonnet --adjudicator codex:gpt-5.4
revise-agent benchmark-run --suite proofbench --mode hybrid-single --reviewer codex:gpt-5.4
revise-agent benchmark-run --suite processbench --mode single-agent --split math --reviewer codex:gpt-5.4-mini
revise-agent benchmark-history
revise-agent benchmark-history --suite writing --limit 10
revise-agent benchmark-history --output benchmarks/history.md
```

Supported unified benchmark modes:

- `deterministic-only`
- `single-agent`
- `single-agent-self-check`
- `multi-agent-cross-check`
- `hybrid-single`
- `hybrid-cross`

Role arguments accept `provider[:model]`, for example `codex:gpt-5.4` or `claude:sonnet`.

Supported unified benchmark suites:

- `math-cases`
- `proofnet`
- `proofbench`
- `processbench`
- `all`

## Output

Each unified review run creates:

- `reviews/<stem>-unified-<timestamp>/summary.md` — top-level summary linking both lanes
- `reviews/<stem>-unified-<timestamp>/summary.json`
- `reviews/<stem>-unified-<timestamp>/writing/` — full writing-review output
- `reviews/<stem>-unified-<timestamp>/math/` — full math-review output

Each standalone math review run creates:

- `reviews/<timestamp>/summary.md`
- `reviews/<timestamp>/math_report.md`
- `reviews/<timestamp>/math_report.json`
- optional `llm_proof_review_<n>_<provider>.md` files when proof-obligation review is enabled
- optional `llm_proof_adjudication_<n>_<provider>.md` files when multi-provider proof review is enabled

Each standalone writing review run creates:

- `reviews/<timestamp>/summary.md`
- `reviews/<timestamp>/final_report.md`
- `reviews/<timestamp>/final_report.json`
- `reviews/<timestamp>/basic_<provider>.md`
- `reviews/<timestamp>/structure_<provider>.md`
- `reviews/<timestamp>/venue_<provider>.md`
- matching `.json` metadata files for each role output

The local writing benchmark suite creates:

- `benchmarks/writing_cases/runs/<timestamp>/benchmark_summary.md`
- `benchmarks/writing_cases/runs/<timestamp>/benchmark_summary.json`
- one subdirectory per benchmark case with writing-review artifacts

The local math benchmark suite creates:

- `benchmarks/math_cases/runs/benchmark_summary.md`
- `benchmarks/math_cases/runs/benchmark_summary.json`
- one subdirectory per benchmark case with its `math_report.md`

The ProofNet adapter creates:

- `benchmarks/proofnet/<split>/manifest.json`
- `benchmarks/proofnet/<split>/runs/proofnet_benchmark_summary.md`
- `benchmarks/proofnet/<split>/runs/proofnet_benchmark_summary.json`
- one subdirectory per imported ProofNet case with its `math_report.md`

The ProofBench adapter creates:

- `benchmarks/proofbench/train/manifest.json`
- imported `.tex` cases built from competition problems plus model-generated proofs
- benchmark summaries that preserve `expert_rating` metadata and report simple issue-score aggregates

The ProcessBench adapter creates:

- `benchmarks/processbench/<split>/manifest.json`
- imported `.tex` cases where each reasoning step is rendered as `Step n: ...`
- benchmark summaries that report exact first-error-step accuracy against the dataset label

The unified benchmark runner creates:

- `benchmarks/runs/<suite>-<mode>-<timestamp>/benchmark_summary.md`
- `benchmarks/runs/<suite>-<mode>-<timestamp>/benchmark_summary.json`
- one subdirectory per benchmark case with its `math_report.md`
- optional `llm_proof_self_check_<n>_<provider>.md` files in self-check mode
- optional `llm_proof_adjudication_<n>_<provider>.md` files in cross-check mode

Every `benchmark-math` and `benchmark-writing` run also appends a provenance entry to `benchmarks/registry.jsonl`, recording git commit, prompt template hashes, provider specs, and pass/fail results. Use `revise-agent benchmark-history` to render a comparison report from this registry.

## Fallback Behavior

- If neither `codex` nor `claude` is installed, `revise-agent review` exits with an explicit environment error.
- If only one provider is available, ReviseAgent prints a warning and switches to `single-provider-self-verify` mode.
- If the final adjudication step fails, ReviseAgent falls back to a merged single report instead of leaving the user with no final artifact.

## Notes

- The POC sends the LaTeX content directly to each CLI through stdin instead of asking the model to read files from disk. This keeps the first end-to-end path simpler and more deterministic.
- The review rubric emphasizes writing issues first, then mathematical errors, then notation and LaTeX hygiene.
- The writing-review lane is intentionally layered: basic language hygiene, structure/logic, and venue-style alignment are reviewed separately before final adjudication.
- The deterministic math lane is intentionally narrow. It currently targets simple function definitions, definite integrals, average-value claims, and obvious continuity failures.
- The theorem/proof layer is also intentionally lightweight. It does not certify a proof as correct; it only extracts theorem/proof structure and highlights likely weak proof steps.
- Optional LLM proof review is advisory only. It is meant to help surface suspicious proof obligations, not to certify a theorem as correct.
- In multi-provider math mode, ReviseAgent prefers adjudicated proof findings over raw per-provider duplicates.
- The initial external benchmark adapter targets the official ProofNet benchmark JSONL files and turns a small slice into local `.tex` cases for structural math-review evaluation.
- The unified benchmark runner separates orchestration mode from model choice, so the same suite can be re-run under deterministic, single-agent, self-check, cross-check, and hybrid settings.
- `ProofBench` is currently used as a proof-review benchmark with expert-rating metadata preserved; the first metric is issue-score aggregation rather than a full grading model.
- `ProcessBench` is currently used as a step-verification benchmark, comparing the earliest flagged `Step n` against the dataset's labeled first wrong step.
- The writing-review lane currently uses prompt-specialized multi-agent coordination rather than a deterministic parser. It is designed to surface revision priorities, not to rewrite a paper automatically.
- Word support is intentionally out of scope for this initial POC.
