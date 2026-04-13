# Revisica Agent Map

Revisica uses specialized agents organized into three lanes. Each agent has a single, focused task within the review pipeline.

```
LaTeX / PDF
    │
    ├── Writing Lane
    │   ├── writing-basic-reviewer
    │   ├── writing-structure-reviewer
    │   ├── writing-venue-reviewer
    │   ├── writing-self-checker
    │   ├── writing-judge
    │   └── polish-agent
    │
    ├── Math Lane
    │   ├── [deterministic] SymPy verification
    │   ├── math-proof-reviewer  (versioned: v0, v1, ...)
    │   ├── math-self-checker
    │   ├── math-adjudicator
    │   ├── math-claim-verifier
    │   ├── notation-tracker
    │   └── formula-cross-checker
    │
    ├── Eval (internal, not part of review pipeline)
    │   └── refine-eval-judge
    │
    └── Merge → Final Report
```

## Writing Lane

| Agent | Task | Input | Output | Tools |
|---|---|---|---|---|
| `writing-basic-reviewer` | Typos, grammar, ambiguous references, terminology consistency | LaTeX full text | JSON findings | Read, Glob, Grep |
| `writing-structure-reviewer` | Paragraph flow, argument progression, contribution framing, claim/evidence alignment | LaTeX full text | JSON findings | Read, Glob, Grep |
| `writing-venue-reviewer` | Style/framing alignment with target venue profile | LaTeX + venue profile | JSON findings | Read, Glob, Grep |
| `writing-self-checker` | Filter false positives from writing review findings | Findings + original text | Filtered JSON findings | Read, Glob, Grep |
| `writing-judge` | Deduplicate, prioritize, merge findings from all writing agents into final report | Multiple findings JSONs | Markdown report | Read, Glob |
| `polish-agent` | Lightweight prose improvement: word choice, flow, transitions (no structural changes) | LaTeX full text | Markdown with before/after rewrites | Read, Glob |

**Flow**: `basic + structure + venue` → `self-checker` → `judge` → final writing report

## Math Lane

| Agent | Task | Input | Output | Tools |
|---|---|---|---|---|
| `math-proof-reviewer` | Verify each proof step for logical/computational correctness; find the first error | Theorem + proof obligations | JSON findings | Read, Glob, Grep, Bash (v1), WebSearch (v1), WebFetch (v1) |
| `math-self-checker` | Filter false positives from proof review | Findings + original text | Filtered JSON findings | Read, Glob, Grep |
| `math-adjudicator` | Merge proof review findings from multiple providers (Claude + Codex) into single verdict | Multiple provider findings | Merged JSON findings | Read, Glob, Grep |
| `math-claim-verifier` | Write and run Python/SymPy code to computationally verify specific mathematical claims | A specific claim | JSON findings + verification code | Read, Glob, Grep, **Bash** |
| `notation-tracker` | Build symbol table; flag undefined symbols, redefinitions, notation drift | LaTeX full text | JSON findings | Read, Glob, Grep |
| `formula-cross-checker` | Compare formulas between theorem statements, proofs, and discussion text for consistency | LaTeX full text | JSON findings | Read, Glob, Grep |

**Flow**: `deterministic SymPy` + `proof-reviewer` (per blueprint) → `self-checker` or `adjudicator` → merge with deterministic results

**Deterministic checks** (no LLM, pure SymPy):
- Integral equality: `∫_a^b f(x)dx = rhs` verified symbolically
- Average value: `(1/(b-a))∫_a^b f(x)dx` vs claimed value
- Continuity claims: checked via `continuous_domain()`
- Weak justification flagging: "clearly", "obviously", "trivially"

## Eval (Internal)

| Agent | Task | Input | Output | Tools |
|---|---|---|---|---|
| `refine-eval-judge` | Evaluate whether review findings cover expected issues (for Refine.ink benchmark) | Expected issues + actual findings | Match/partial/miss JSON | Read |

Not part of the review pipeline — used only during benchmark evaluation.

## Agent Versioning

Math agents support versioned prompts for benchmark comparison:

- `math-proof-reviewer-v0`: Original minimal prompt (Read/Glob/Grep only)
- `math-proof-reviewer-v1`: Structured reasoning + chain-of-thought + Bash/WebSearch/WebFetch
- `math-proof-reviewer`: Alias for the latest version

Select version via `--agent-version v0` in benchmark runs.

## Key Differences Between Similar Agents

**proof-reviewer vs claim-verifier**: proof-reviewer checks the *reasoning chain* (does step B follow from step A?). claim-verifier checks *individual numerical/algebraic claims* by running code (does ∫₀¹ x² dx = 1/3?).

**self-checker vs adjudicator**: self-checker filters one reviewer's false positives. adjudicator merges findings from *multiple providers* (e.g., Claude and Codex reviewed the same proof).

**writing-judge vs writing-self-checker**: self-checker removes false positives from a single reviewer. judge merges and prioritizes across all writing reviewers into a final report.

## Future Agents (TODO)

- **literature-fact-checker**: Verify cited references exist, check citation context accuracy, flag phantom citations
