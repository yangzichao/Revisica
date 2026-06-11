# Inline Annotations

**Status:** Phases 1–4 implemented (June 2026).

## Problem

Review output was four markdown reports rendered as prose. Findings were
not anchored to the paper: a user reading "notation drift in Section 3"
had to find the passage themselves, and the structured findings JSON each
lane already produced (per-role artifacts, `math_report.json`) was never
exposed to the desktop app.

## Design

```
lanes → collect → anchor (quote-first) → findings.json + document.md
                                              ↓
                    GET /api/results/{run_id}/findings
                                              ↓
            Annotated tab: highlighted document + finding cards
```

### Unified finding (`src/revisica/findings/`)

Both lanes are converted into one `UnifiedFinding` shape
(`lane, role, provider, category, severity, title, explanation, fix,
evidence, status, anchor`). Severity is normalized onto
`critical / major / minor / info`.

### Quote-first anchoring

LLM-reported line numbers are unreliable; verbatim quotes are not. The
anchor resolver works in tiers:

1. **exact** — the reviewer's `snippet` (or its longest line ≥ 20 chars)
   is matched whitespace-insensitively against the document text; the
   anchor gets char offsets + line number + section id. Repeated matches
   pick the occurrence nearest the hinted line.
2. **line** — no quote match but the lane reported a valid line number
   (deterministic math checks always do); the anchor covers that line.
3. **unresolved** — shown in the sidebar without an in-document mark.

The anchored text is the *normalized markdown the review ran against*
(`document.markdown` from ingestion, the raw file as fallback), persisted
as `document.md` next to `findings.json` so offsets always have their
reference text. For reviews started from the Library, this is the same
markdown the app already displays.

### API

`GET /api/results/{run_id}/findings` → findings.json payload +
`document_markdown`. 404 for runs predating the artifact — the app
simply hides the tab.

### Desktop app (`desktop/.../pages/Jobs/annotated/`)

- **Annotated tab** is the default landing tab when findings exist.
- The document is rendered with the same ReactMarkdown stack as the
  Library preview, plus a rehype plugin stamping `data-line` on every
  element (markdown AST positions), which maps findings to rendered
  blocks.
- **Block marks**: severity-colored left rule + tint on the anchored
  block. **Exact-quote marks**: character-precise paint via the CSS
  Custom Highlight API (no DOM mutation; KaTeX's hidden MathML mirror is
  excluded from matching). Quotes containing raw LaTeX fall back to the
  block mark.
- Two-way sync: clicking a finding card scrolls the document; clicking a
  highlighted block activates (and cycles through) its findings.
- Severity filter chips with counts.

## Acceptance criteria — all verified

- [x] Unified run writes `findings.json` + `document.md`; failures append
      a run warning instead of failing the review.
- [x] Deterministic math findings anchor `exact` on `minimal_paper.tex`
      (e2e: 2/2 exact with section ids).
- [x] `pytest tests/test_findings.py` — 16 tests covering anchor tiers,
      occurrence disambiguation, sorting, collect, severity, persistence.
- [x] Benchmark artifact formats unchanged
      (`benchmark-run --suite math-cases --mode deterministic-only` 5/5).
- [x] Desktop typecheck + build pass; visual check in the built renderer
      confirmed highlights, scroll sync, filters, evidence cards.

## Phase 4 — counterexample probing (implemented)

`math_check/probe.py` adds numeric falsification feeding the same finding
pipeline:

- **Bounded inequality claims** ("f(x) ≤ g(x) for all x ∈ [a,b]", display
  or inline form; only extracted when the interval is explicit). A
  rational grid is sampled and every hit is confirmed by *exact*
  substitution, so the witness in `evidence` ("At x = 2, the left side is
  8 and the right side is 2") is machine-checkable, never float noise.
  Exact equality refutes strict relations only. With no counterexample,
  a symbolic extremum proof (`sp.minimum` of the gap) upgrades the claim
  to machine-verified; inconclusive claims stay silent.
- **Numeric quadrature fallback for integrals** with no closed form —
  previously `integrate` returning unevaluated would have refuted a
  correct claim.
- `parse_expr` now retries with sympy's implicit-multiplication
  transformation, so LaTeX-style `2x` parses.

Benchmark cases `wrong_inequality` / `correct_inequality` added to the
math-cases suite (7/7 PASS). Remaining future work: tool-grounded proof
review (lets LLM proof reviewers call SymPy mid-review; prompt-content
change, kept out of this structural pass per conventions).
