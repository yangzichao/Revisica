# Feature Specs (Design Docs)

This directory holds **feature specs** in the style of a Google-style design doc: how a feature works, what it touches, and how we know it's done. Specs describe the *how*; **decisions** (why X over Y) live in [`../decisions/`](../decisions/README.md) as ADRs.

## When to write a spec

Write one when **all three** are true:
1. The change spans multiple files or modules, or introduces a new subpackage.
2. There is a design worth capturing — data flow, interfaces, state transitions — that a PR description cannot carry.
3. You want acceptance criteria that outlive the PR.

**Skip** for:
- Bug fixes → `docs/bugs.md` + PR.
- One-off task tracking → `docs/todo.md`.
- Post-hoc lessons → `docs/learning/YYYY-MM-DD-<slug>.md`.
- Pure refactors → just do them, or list in `docs/architecture-refactor-todo.md`.
- A library/schema *choice* with no accompanying design → write an ADR in `docs/decisions/` instead.

Rule of thumb: if the PR description would be enough, skip the spec. If the design pivots on a non-obvious choice, extract that choice into an ADR and have the spec link to it.

## Format

Copy [ingestion-parsers.md](ingestion-parsers.md) as a template — it is the cleanest example in the repo (89 lines, all acceptance criteria testable, linked to real commits). Avoid copying [dmg-packaging.md](dmg-packaging.md) (too long) or [desktop-app.md](desktop-app.md) (no runnable acceptance criteria).

Required sections (mandated by `CLAUDE.md`):

1. **Status** — exactly one of `draft | approved | done`. No parentheticals.
2. **Problem** — what's missing or broken, with a concrete symptom or user story. Not a feature wish.
3. **Design** — the chosen approach. Include an ASCII data-flow diagram if data is transformed. Link any ADR the design depends on: `Decision: docs/decisions/NNNN-…`.
4. **Implementation plan** — numbered checklist of commits/PRs the reader can tick off.
5. **Acceptance criteria** — *runnable* checks. "Pytest X passes" beats "module is well-designed." If criteria can't be run, the spec is not ready to approve.

Optional sections:

6. **Open Questions** — each tagged `[blocks approval]` or `[resolve during implementation]`.
7. **References** — links to `docs/learning/` entries that justified this spec, related specs, and ADRs.

## Status lifecycle

Three states, each with an explicit gate:

| Status | Gate to enter | Meaning |
|---|---|---|
| `draft` | File exists, Problem + Design written | Design is being sketched; Open Questions are active |
| `approved` | No `[blocks approval]` questions; Implementation plan has concrete steps | Ready to implement; should happen within ~1 week or mark as blocked |
| `done` | All Implementation checkboxes ticked; every Acceptance Criterion has verification evidence (test name, benchmark %, commit SHA) | Feature is shipped; spec becomes historical record |

Abandoned specs: delete the file or move it to `docs/specs/archived/`. Don't leave dead specs as `draft` forever.

## Spec vs. ADR vs. Learning

| Artifact | Answers | Mutability | Example |
|---|---|---|---|
| **ADR** (`docs/decisions/`) | "Why did we pick X over Y?" | Immutable once Accepted; superseded by a new ADR | "Use MinerU as default PDF parser" |
| **Spec** (`docs/specs/`) | "How does feature F work, and when will we know it's done?" | Lives until shipped; frozen when `done` | "Multi-format ingestion parsers" |
| **Learning** (`docs/learning/`) | "What did running the system teach us?" | Append-only; each entry is timestamped and frozen | "Focused prompt beats whole paper" |

A single feature often produces **all three**:
- An ADR captures the choice it pivots on.
- A spec describes the feature that uses the decision.
- One or more learning notes, written after shipping, validate or challenge the decision.

## Linking conventions

- Spec → ADR: in the Design section — `Decision: docs/decisions/NNNN-<slug>.md`.
- Spec ← Learning: a post-ship learning that validates the spec links back — `Validates: docs/specs/<slug>.md`.
- Spec → Learning: if a learning triggered the spec, link it in References — `Triggered by: docs/learning/YYYY-MM-DD-<slug>.md`.
- Todo ↔ Spec: open specs are linked from `docs/todo.md` so the tracker stays the source of truth for "what's next."
- Superseded specs: mark the old spec `done` (if shipped) or move to `archived/` (if abandoned), and the new spec references it in References.

## Index

| Feature | Status |
|---|---|
| [Multi-format ingestion parsers](ingestion-parsers.md) | `done` |
| [Desktop app architecture](desktop-app.md) | `approved` |
| [DMG packaging](dmg-packaging.md) | `draft` |
| [Proof statement checker](proof-statement-checker.md) | `draft` |
