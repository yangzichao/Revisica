# Python Agent Orchestration Frameworks: Best Choice for Multi-Provider HITL Desktop App (2025-2026)

## Direct Answer

**LangGraph is the correct choice** for this use case. No other framework satisfies all five hard constraints simultaneously: multi-provider (Claude + OpenAI), human-in-the-loop with pause/resume, dynamic DAG routing, parallel execution, and streaming to an external GUI. The second-best option is PydanticAI — slimmer, type-safe, excellent multi-provider support, but its HITL story is weaker and the graph-based execution model is newer and less battle-tested.

---

## Framework-by-Framework Evaluation

### 1. LangGraph (LangChain)

**Multi-provider:** Full. Works with OpenAI, Anthropic, Ollama, Mistral, any provider that implements the LangChain chat model interface. No lock-in.

**Tool use:** Full. Native tool-calling abstraction works identically across providers.

**Human-in-the-loop:** First-class. The canonical HITL framework among all options evaluated. Pattern: graph pauses at an `interrupt` node, persists full state to a checkpointer (SQLite for local, PostgreSQL for production), waits indefinitely, resumes from the exact paused node when the user responds. No thread blocking. State survives process restarts.

**Dynamic/conditional routing:** Core design primitive. Edges can be conditional functions (Python callables) that inspect state and return the next node name. The graph can be built programmatically at runtime, making it a true dynamic DAG.

**Parallel execution:** Supported natively via parallel branches (fan-out to multiple nodes, fan-in with a reducer). Works transparently on top of asyncio or ThreadPoolExecutor. You can replace your current 12-worker ThreadPoolExecutor with a LangGraph parallel branch subgraph.

**Dependency weight:** Heavy. Pulls in the full LangChain stack. Cold import is slow. This is the real cost. For a desktop app shipping via Electron + FastAPI, bundle size matters. Mitigatable: ship a pre-activated venv, lazy-import the module, or containerize the backend.

**Production maturity:** LangGraph 1.0 shipped October 2025 — the first stable semver release in the AI agent framework space. Used at scale by enterprises. LangSmith provides tracing, cost tracking, and replay debugging that no other framework matches for production observability.

**Streaming:** Comprehensive. `graph.astream_events()` emits node transitions, LLM token deltas, tool call start/end, and state diffs. You can pipe these events directly to a FastAPI SSE endpoint and consume them in Electron. The v2 event format (stable in LangGraph 1.0) is clean and documented.

**Verdict for your use case:** Satisfies all eight criteria. The dependency weight is the only real cost.

---

### 2. PydanticAI

**Multi-provider:** Excellent. Native `OpenAIChatModel`, `AnthropicModel`, `GoogleModel`, plus 20+ others via LiteLLM. Single agent portable across providers by swapping one constructor argument. `FallbackModel` for automatic failover.

**Tool use:** Full, with automatic Pydantic validation of tool arguments and results.

**Human-in-the-loop:** Weak. No built-in pause/resume mechanism as of early 2026. You'd build it yourself using a database to persist run state, which is non-trivial.

**Dynamic routing:** Supported via a graph module added in v1.0 (`pydantic_ai.graph`). Younger API, less community documentation than LangGraph.

**Parallel execution:** Supported via `ConcurrencyLimitedModel` wrapper and standard asyncio. Multi-agent patterns (delegation, handoffs) are documented.

**Dependency weight:** Light relative to LangGraph. The core `pydantic-ai` package has minimal transitive dependencies. No LangChain required.

**Production maturity:** v1.0 released September 2025 with API stability commitment. 16k+ GitHub stars by early 2026, weekly releases. Still newer than LangGraph; fewer production war stories.

**Streaming:** First-class. Streamed structured output with real-time Pydantic validation is a differentiating feature.

**Verdict:** Best choice if you are willing to build HITL yourself and prefer a leaner dependency tree. For Revisica specifically, HITL is a stated requirement — this gap is significant.

---

### 3. OpenAI Agents SDK

**Multi-provider:** No. Locked to OpenAI models. Disqualified by your requirement to use Claude.

**Tool use:** Full.

**HITL:** Supported via the handoff mechanism but not as a first-class pause/resume pattern.

**Parallel execution:** No. Linear handoff chains only.

**Verdict:** Disqualified. Vendor lock-in to OpenAI is incompatible with your architecture.

---

### 4. Anthropic Agent SDK (claude_agent_sdk)

**Multi-provider:** No. Locked to Anthropic/Claude models. Disqualified by your requirement to use GPT.

**Tool use:** Full, with the deepest MCP (Model Context Protocol) integration of any framework.

**HITL:** Not documented as a first-class feature.

**Verdict:** Disqualified. Vendor lock-in to Anthropic is incompatible with your architecture.

---

### 5. CrewAI

**Multi-provider:** Yes, via LiteLLM. Supports OpenAI, Anthropic, and others.

**Tool use:** Full, role-based agent tool assignment.

**HITL:** Weak. No robust pause/resume checkpointing. The "human input" feature is a synchronous `input()` call in the terminal — not suitable for a GUI-driven desktop app.

**Dynamic routing:** Limited. The role-based DSL is intuitive for fixed crew topologies but becomes awkward for conditional DAGs.

**Parallel execution:** Good. Automatic task dependency resolution enables parallel crew execution.

**Dependency weight:** Moderate-heavy.

**Production maturity:** 45,900+ GitHub stars. Fortune 500 adoption for fixed-topology workflows. But the comparison of "teams start with CrewAI for prototyping then migrate to LangGraph for production" is widely repeated in the 2025 literature and matches the pattern here.

**Verdict:** Good for fixed-topology multi-role pipelines. Not suitable for your use case because HITL is not production-grade and conditional dynamic routing is constrained.

---

### 6. AutoGen / AG2 (Microsoft)

**Multi-provider:** Yes, supports multiple providers.

**Tool use:** Full.

**HITL:** Reasonably strong — designed for conversational agent loops that can pause for human input mid-conversation.

**Dynamic routing:** Yes, event-driven GroupChat architecture allows dynamic transitions.

**Parallel execution:** Asynchronous event-driven architecture reduces blocking.

**Dependency weight:** Moderate.

**Production maturity:** Well-established, Microsoft-backed. AG2 is the community fork with active development. However, the "20 LLM calls minimum" overhead reported for some workflows makes it expensive for high-throughput pipelines like yours.

**Streaming:** Less mature than LangGraph for external GUI streaming.

**Verdict:** Viable but suboptimal. The overhead per-call and the weaker streaming story make it a worse fit than LangGraph for a FastAPI + Electron GUI consumer.

---

### 7. Temporal / Prefect (workflow engines)

**Multi-provider:** Agnostic to LLM providers — these are general compute orchestrators, not AI-specific.

**Tool use:** Yes, but you define "tools" as workflow activities manually. No LLM tool-calling abstraction.

**HITL:** Temporal has first-class human signal support (workflow waits for a signal, resumes on receipt). This is arguably more robust than LangGraph's checkpointer for extremely long-running or mission-critical flows.

**Dynamic routing:** Yes, workflows can branch dynamically.

**Parallel execution:** Excellent. Temporal is designed for durable parallel compute at scale.

**Dependency weight:** Heavy operational overhead. Temporal requires a running server (self-hosted or Temporal Cloud). Prefect is lighter but still non-trivial.

**Production maturity:** Battle-tested for production at scale (e.g., Netflix, Stripe use Temporal). But the operational complexity is inappropriate for a desktop app.

**Key finding (2026):** Practitioners combine Temporal (durability, intra-node checkpointing) with LangGraph (agent reasoning logic) for production-critical systems. The combination solves LangGraph's known weakness: state is only saved between nodes, not within a node — meaning a 10,000-item for-loop inside a single node loses all progress on failure. For Revisica's use case (paper review, not 10k-item batch), this edge case is unlikely to matter.

**Verdict:** Not recommended as a standalone replacement for a desktop app. Temporal adds server infrastructure that is wrong for this deployment model. If Revisica ever needs enterprise-scale durability, consider Temporal wrapping LangGraph later.

---

## Ordered Ranking for Your Specific Use Case

| Rank | Framework | Reason |
|---|---|---|
| 1 | **LangGraph** | Satisfies all 8 criteria. Production-proven HITL, full streaming, dynamic DAG, multi-provider. Dependency weight is the only cost. |
| 2 | **PydanticAI** | Best multi-provider + type safety + light deps. Blocked by absent first-class HITL. Best fallback if you build HITL yourself. |
| 3 | **AutoGen/AG2** | Viable multi-provider + HITL. Heavier per-call overhead, weaker streaming story. |
| 4 | **CrewAI** | Good for prototyping fixed crews, not for GUI-driven HITL desktop apps. |
| 5 | **Temporal** | Production durability champion but requires server infrastructure; wrong for desktop. |
| 6 | **OpenAI Agents SDK** | Disqualified: OpenAI-only. |
| 7 | **Anthropic Agent SDK** | Disqualified: Anthropic-only. |

---

## Migration Path for Revisica

Your current architecture (ThreadPoolExecutor with 12 workers, conditional routing in Python, manual state passing between writing and math lanes) maps cleanly onto LangGraph:

1. Each "lane" (writing, math) becomes a subgraph.
2. The `unified_review.py` orchestrator becomes the top-level graph with two parallel branches.
3. `review.py` subprocess calls (codex/claude CLIs) become LangGraph tool nodes.
4. The current ThreadPoolExecutor parallel fan-out becomes native LangGraph parallel branches.
5. HITL gates (e.g., "user reviews findings before final report") become `interrupt()` nodes with a persistent SQLite checkpointer (zero infrastructure, ships with the desktop app).
6. Streaming to the Electron frontend: FastAPI SSE endpoint consuming `graph.astream_events()`.

The one architectural decision to make upfront: LangGraph's checkpointer requires a persistence backend. For desktop, `SqliteSaver` (bundled, no server) is the right choice. For a future server deployment, swap to `AsyncPostgresSaver` without changing any graph logic.

---

## Confidence & Caveats

**Confidence: High.** Multiple independent sources (Langfuse benchmark, MorphLLM framework comparison, gurusup.com 2026 multi-agent guide, LangGraph 1.0 release notes) converge on LangGraph as the production standard for multi-provider HITL DAG agents in Python. The one genuine uncertainty is dependency weight for Electron packaging — worth a spike test before committing.

The framework landscape is moving fast: PydanticAI's graph module is young and could close the HITL gap within 2026. If bundle size becomes a blocker, revisit PydanticAI at that point.

---

## Sources

- [AI Agent Frameworks in 2026: 8 SDKs, ACP, and the Trade-offs Nobody Talks About — MorphLLM](https://www.morphllm.com/ai-agent-framework)
- [Comparing Open-Source AI Agent Frameworks — Langfuse](https://langfuse.com/blog/2025-03-19-ai-agent-comparison)
- [Best Multi-Agent Frameworks in 2026: LangGraph, CrewAI — Gurusup](https://gurusup.com/blog/best-multi-agent-frameworks-2026)
- [LangGraph 1.0 released in October 2025 — Medium](https://medium.com/@romerorico.hugo/langgraph-1-0-released-no-breaking-changes-all-the-hard-won-lessons-8939d500ca7c)
- [LangGraph vs Temporal for AI Agents: Durable Execution Architecture Beyond For Loops — Medium/Data Science Collective](https://medium.com/data-science-collective/langgraph-vs-temporal-for-ai-agents-durable-execution-architecture-beyond-for-loops-a1f640d35f02)
- [PydanticAI Models Overview — Official Docs](https://ai.pydantic.dev/models/overview/)
- [AI Framework Comparison 2025: OpenAI Agents SDK vs Claude vs LangGraph — Enhancial](https://enhancial.substack.com/p/choosing-the-right-ai-framework-a)
- [Beyond input(): Building Production-Ready Human-in-the-Loop AI Agents with LangGraph — DEV Community](https://dev.to/sreeni5018/beyond-input-building-production-ready-human-in-the-loop-ai-with-langgraph-2en9)
- [How to Build Human-in-the-Loop Agents with LangGraph and Streamlit — MarkTechPost](https://www.marktechpost.com/2026/02/16/how-to-build-human-in-the-loop-plan-and-execute-ai-agents-with-explicit-user-approval-using-langgraph-and-streamlit/)
- [14 AI Agent Frameworks Compared — Softcery](https://softcery.com/lab/top-14-ai-agent-frameworks-of-2025-a-founders-guide-to-building-smarter-systems)
