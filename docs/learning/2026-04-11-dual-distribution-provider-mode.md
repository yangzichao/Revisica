# Learning: Dual Distribution Requires Provider Mode Abstraction

**Date:** 2026-04-11 (session 2)
**Commit:** (this session)
**Context:** Planning Mac App Store vs DMG distribution, discovered hard sandbox constraint.

## The Observation

Mac App Store sandbox **completely blocks** `child_process.exec` to user-installed binaries (`codex`, `claude`). This is a hard Apple restriction, no workaround. Meanwhile, Claude Max / ChatGPT Pro subscriptions **cannot** be accessed via HTTP API — they only work through the official CLIs.

This creates a fundamental split:

| Distribution | Provider backend | Auth | Cost to user |
|---|---|---|---|
| DMG (notarized) | CLI (`codex`/`claude`) | Subscription login | $0 (included in subscription) |
| App Store | HTTP API (`anthropic`/`openai`) | API key | Per-token billing |

## The Lesson

**Distribution target determines provider backend — this must be a first-class config, not a runtime accident.**

Before this session, the alias `"claude"` was hardcoded to `"claude-cli"`. If we shipped an App Store build, it would silently fail on every LLM call. The fix is a `backend_mode` flag that controls alias resolution:

- `cli` mode: `claude` → `claude-cli` (shells out to CLI)
- `api` mode: `claude` → `anthropic-api` (HTTP API)
- `auto` mode: prefer CLI if available, fall back to API

The key insight: **the upper-layer code should never know or care which backend is active.** It just says `get_provider("claude")` and the registry resolves based on mode.

## Architecture Implications

1. **Provider aliasing must be dynamic, not static.** Hardcoded alias tables are a distribution-mode bug waiting to happen.

2. **Two distribution channels = two install/onboarding flows.** DMG users need `codex`/`claude` CLI installed. App Store users need API keys. The Settings page only matters for `api` mode.

3. **Subscription access is CLI-only for both Anthropic and OpenAI.** As of April 2026, neither company offers a way to programmatically access subscription quota without their official CLI. Anthropic actively blocks third-party proxies. This is unlikely to change — plan around it.

4. **Python 3.9 is a real constraint.** System Python on macOS is 3.9.6. Both `langgraph>=1.0` and PEP 604 union syntax (`str | None`) break on 3.9. Either bump `requires-python` to `>=3.10` or keep 3.9-compatible code in all runtime paths. LangGraph should stay an optional dep until graphs are in the critical path.
