# Learning Log

Timestamped insights from experiments, benchmark runs, and debugging sessions. Each entry captures a non-obvious lesson and its architecture implications.

## Index

| Date | File | Key Insight |
|---|---|---|
| 2026-04-11 | [refactor-lessons-desktop-app](2026-04-11-refactor-lessons-desktop-app.md) | Wrap first, decompose later. Registry pattern for dispatch. One definition, many translations. Silent fallback = invisible bug. Self-review catches different bugs than inline review. |
| 2026-04-07 | [focused-prompt-beats-whole-paper](2026-04-07-focused-prompt-beats-whole-paper.md) | Smaller context + precise question outperforms larger context + vague question. The bottleneck is prompt construction, not model capability. |

## Template

New entries should follow the format: `YYYY-MM-DD-<descriptive-slug>.md` with sections: Date, Commit, Context, Observation, Lesson, Architecture Implications. See the 2026-04-07 entry as a reference.
