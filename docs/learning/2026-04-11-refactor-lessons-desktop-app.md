# Learning: Desktop App Refactor — Architecture Lessons

**Date:** 2026-04-11
**Commit:** `d75e244` through `c5daf8a` (7 commits)
**Context:** Major refactor to support desktop app: ingestion layer, provider abstraction, LangGraph graphs, FastAPI server, Electron shell.

## The Observation

Refactoring a 30-file CLI tool into a modular desktop app architecture revealed several patterns about how code accumulates technical debt, and what makes refactoring safe.

### 1. Provider dispatch was the biggest hidden coupling

The old `review.py` had `if provider == "codex": ... elif provider == "claude": ...` branching that was copied into every call site. Extracting this to a registry (`ProviderRegistry`) reduced `review.py` from 636 to 371 lines and made adding new providers (API key, Ollama) zero-touch for existing code.

**The coupling wasn't in the branching itself — it was in the `PlatformStatus` object being threaded through every function.** After the refactor, `_run_provider()` still accepts `platform` as a parameter but ignores it. Removing this dead parameter is blocked by the number of call sites (bugs.md #5).

### 2. Agent definitions had triple maintenance cost

Three locations defined the same agents in different formats:
- `.claude/agents/*.md` (10 files, dead — not loaded by any code)
- `agents/claude/*.json` (12 files, active)
- `agents/codex/*.md` (11 files, active but missing 2)

The missing files (bug #3) went undetected because only Claude was being used in benchmarks. **If something must be maintained in N places, eventually N-1 of them will drift.** The unified `AgentDefinition` type in `src/revisica/agents/definitions/` solves this by defining once and translating per-provider.

### 3. Silent exception swallowing hides systematic failures

Six `except Exception:` blocks (bug #4) silently fall back to degraded behavior. This is correct for robustness — a failed self-check shouldn't kill the review. But when self-check fails 100% of the time due to a config error, nobody notices because there's no logging.

**Lesson: fallback behavior is good; invisible fallback behavior is a bug.** Every `except Exception:` should at minimum `logging.warning()`.

### 4. LangGraph adoption is incremental, not big-bang

The initial plan was to rewrite all orchestration as LangGraph graphs at once. In practice, the correct approach was:

1. Create graph structure that wraps existing functions as single nodes
2. Verify the graph compiles and can be invoked
3. Incrementally decompose large nodes into smaller ones

The writing graph currently wraps `review_writing_file()` (846 lines, ThreadPoolExecutor inside) as a single node. This is fine — it preserves behavior while establishing the graph skeleton. Decomposing it is a separate step.

**Don't rewrite working orchestration. Wrap it, then incrementally decompose.**

### 5. Self-review catches real bugs

Two self-review rounds found 8 issues:
- 1 critical: nested brace parsing in tex_parser (data loss)
- 2 medium: missing grep file extensions, missing serve error handling
- 2 low: redundant extraction in math graph, thread-unsafe singleton
- 3 trivial: unused imports

The critical bug (nested braces) would have silently truncated paper titles. **Self-review after coding, not during, catches a different class of bugs** — integration issues and edge cases that aren't visible when writing individual functions.

## Architecture Implications

### For future refactoring

- **Wrap first, decompose later** — When migrating orchestration (ThreadPoolExecutor → LangGraph), wrap the old function as a single node first. Only decompose after the graph skeleton works.
- **Registry pattern for any dispatch** — Anywhere you see `if type == "A": ... elif type == "B": ...`, consider a registry. It makes adding new types zero-cost.
- **One definition, many translations** — Agent definitions, provider configs, and any other per-variant data should have one source of truth with translators, not N copies.

### For code quality

- **Every `except Exception:` gets a `logging.warning()`** — No exceptions.
- **Self-review is a separate step** — Do it after completing a batch of work, not inline. Use an explorer agent to find issues systematically.
- **File size limit: 300 lines** — Enforced in this refactor. The largest new file is 206 lines (graphs/unified.py). The legacy 846-line writing_review.py is now explicitly a decomposition target.
