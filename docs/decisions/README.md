# Architecture Decision Records

This directory holds **ADRs** — short, immutable records of non-obvious technical choices. Format follows [Michael Nygard's original ADR template](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions) (2011), used widely across the industry.

ADRs answer **"why did we pick X over Y?"** for a future reader (including a future you) who cannot reconstruct the reasoning from code alone.

## When to write an ADR

Write one when **all** are true:
- A real alternative existed and was considered (even briefly).
- The choice has consequences the reader will want to audit later: a library, data format, schema, dependency, deprecation, packaging strategy, provider routing rule.
- A fresh engineer reading the code cannot infer the reasoning from it.

**Skip** if:
- The answer was obvious (no real alternative).
- It's a taste-level preference.
- It's a transient workaround (log in `docs/bugs.md` or leave a code comment).
- It's *how* a feature works (that's a spec — see `../specs/README.md`).

Rule of thumb: if, six months from now, someone might ask "why MinerU and not Marker?" or "why this schema?" — write an ADR.

## Format

Four sections, one page typical. Copy [0001-pdf-parser-mineru.md](0001-pdf-parser-mineru.md) as a working example.

```markdown
# NNNN. <short imperative noun phrase>

**Status:** Proposed | Accepted | Deprecated | Superseded by NNNN
**Date:** YYYY-MM-DD

## Context

The forces at play: technical constraints, prior choices, deadlines, team structure.
Describe the problem before the decision, not after.

## Decision

"We will <do X>." Active voice. One paragraph is often enough.

## Consequences

What becomes easier, harder, newly risky. Include rejected alternatives with a
one-line reason each — rejection reasons age better than acceptance reasons.
```

If an ADR grows past ~2 pages, it probably contains a design. Split: ADR stays for the *what and why*; a spec in `../specs/` covers the *how*.

## Numbering and immutability

- Sequential, zero-padded integers: `0001-`, `0002-`, … `0042-`. **Never renumber.**
- Slugs are short and descriptive: `0001-pdf-parser-mineru.md`, not `0001-decision.md`.
- ADRs are **immutable** once `Accepted`. To change course:
  1. Write a new ADR (`0007. Switch PDF parser to Marker`) referencing the old one.
  2. Edit the old ADR's status line only: `Superseded by 0007`.
  3. Do not rewrite the old ADR's body. Its reasoning is historical record.
- Typo and link fixes are fine. Content changes are not.

## Status lifecycle

| Status | Meaning |
|---|---|
| `Proposed` | Draft, under discussion. Not yet binding. |
| `Accepted` | Decision is in force. Code and other docs should reflect it. |
| `Deprecated` | Decision no longer applies but was not actively replaced (e.g., the feature is gone). |
| `Superseded by NNNN` | A later ADR reversed or replaced this one. |

## Linking

- A spec in `../specs/` that relies on an ADR links it in its Design section: `Decision: docs/decisions/NNNN-…`.
- A learning note in `../learning/` that validates (or contradicts) an ADR links back: `Validates/Challenges: docs/decisions/NNNN-…`.
- An ADR may link the learning(s) that triggered it in its Context section.

## Index

| # | Title | Status | Date |
|---|---|---|---|
| 0001 | [Use MinerU as default PDF parser](0001-pdf-parser-mineru.md) | Accepted | 2026-04-17 |
