# Learning Log

Timestamped insights from experiments, benchmark runs, and debugging sessions. Each entry captures a non-obvious lesson and its architecture implications.

## Index

| Date | File | Key Insight |
|---|---|---|
| 2026-04-12 | [ingestion-parsers-design](2026-04-12-ingestion-parsers-design.md) | "Markdown + LaTeX math" is the lingua franca. MMD = Markdown (no syntax difference). MinerU has two incompatible APIs across 1.x/2.x. Parser isolation → first pytest suite (24 tests, 0.05s). |
| 2026-04-11 | [dual-distribution-provider-mode](2026-04-11-dual-distribution-provider-mode.md) | Mac App Store sandbox blocks CLI calls; subscriptions can't be used via API. Distribution target must be a first-class config (`backend_mode`), not a runtime accident. Python 3.9 is a real constraint. |
| 2026-04-11 | [architecture-debt-observations](2026-04-11-architecture-debt-observations.md) | Half-migration is worse than no migration. 5 new packages built but not wired into main flow = 5 islands + dual maintenance. Complete the migration before building features on top. |
| 2026-04-11 | [refactor-lessons-desktop-app](2026-04-11-refactor-lessons-desktop-app.md) | Wrap first, decompose later. Registry pattern for dispatch. One definition, many translations. Silent fallback = invisible bug. Self-review catches different bugs than inline review. |
| 2026-04-07 | [focused-prompt-beats-whole-paper](2026-04-07-focused-prompt-beats-whole-paper.md) | Smaller context + precise question outperforms larger context + vague question. The bottleneck is prompt construction, not model capability. |

## Template

New entries should follow the format: `YYYY-MM-DD-<descriptive-slug>.md` with sections: Date, Commit, Context, Observation, Lesson, Architecture Implications. See the 2026-04-07 entry as a reference.
