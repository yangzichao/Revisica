# Learning: Half-Migration Architecture Debt

**Date:** 2026-04-11
**Commit:** `29c973c`
**Context:** External review of the refactored codebase identified 5 structural problems, all stemming from the same root cause: the main flow hasn't been migrated to the new architecture yet.

## The Observation

After building 5 new packages (profiles, ingestion, providers, agents, graphs) alongside the existing code, an architecture review found:

1. **Two orchestration layers coexist.** `graphs/` (LangGraph) wraps the old `unified_review.py` → `writing_review.py` (ThreadPoolExecutor) without replacing it. CLI and API both still call the old path.

2. **Two agent systems coexist.** New `agents/definitions/` (Python dataclass `AgentDefinition`, used by graphs/focus.py and graphs/polish.py) lives alongside old `agent_assets.py` + JSON/MD files (used by writing_review.py, math_llm_review.py, benchmark_refine.py). `AgentDefinition` and `AgentSpec` are two different abstractions for the same concept.

3. **Ingestion layer is an island.** `RevisicaDocument` with its section tree and metadata isn't consumed by the review pipeline. `writing_review.py` does its own section extraction. `math_review.py` reads raw `.tex` directly.

4. **Two prompt systems.** `templates.py` (~470 lines) has prompt builders + venue profiles. `agents/definitions/*.py` has system prompts. No unified prompt management strategy.

5. **Provider layer done, upper layers not updated.** `providers/` has clean `BaseProvider` → registry. But `review.py` still has `_run_provider(name, platform, ...)` where `platform` is ignored. `writing_review.py` imports the private `_run_provider_agent`.

## The Lesson

**"Wrap first, decompose later" has a shelf life.**

The incremental strategy (build new alongside old, switch over gradually) is correct for the first iteration. But the half-migrated state creates **dual maintenance cost immediately** — every new feature must work with both systems, and every bug fix must be applied in both places.

The critical insight: **the migration must be completed before building features on top of it.** Otherwise:
- HITL (P2) needs to work with both orchestration systems
- Settings page (P1) needs to work with both agent systems
- PDF support needs to work with both ingestion paths

**Decision: P0 is now "complete the migration", not "build more features."**

### Specific lessons

1. **Don't build N packages in parallel without wiring them.** We built 5 packages but didn't connect them to the main flow. This created 5 islands instead of 1 architecture.

2. **The "bridge type" pattern is key.** `AgentDefinition` (new) needs a translator to `AgentSpec` (old) so new code can call old code. Without this translator, the two systems can't interoperate, and you end up maintaining both.

3. **Thin wrapper graphs are not migration.** `graphs/writing.py` wrapping `review_writing_file()` as a single node gives the appearance of LangGraph adoption without any of the benefits (HITL, streaming, dynamic routing). It's a checkpoint, not a destination.

4. **Prompt management needs a clear owner.** Static agent instructions (system prompt) → `agents/definitions/`. Dynamic task construction (file paths, venue profiles, findings content) → graph nodes or templates. Venue profile definitions → profiles package. This split must be explicit.

## Architecture Implications

The P0 migration order matters:

```
P0.1: Agent translators (AgentDefinition → AgentSpec bridge)
  ↓
P0.2: Wire ingestion (RevisicaDocument consumed by pipeline)
  ↓
P0.3: Wire graphs (LangGraph replaces ThreadPoolExecutor)
  ↓
P0.4: Delete old agent system (agent_assets.py, JSON/MD files)
  ↓
P0.5: Clean review.py (remove dead platform param)
  ↓
P0.6: Unify prompts (templates.py + agents/definitions/)
```

Each step has a clear verification: run the math benchmark (5/5 must pass) and spot-check `revisica review examples/minimal_paper.tex`.

**The half-migrated state is now the #1 risk.** Every day it persists, the two systems diverge further.
