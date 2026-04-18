# Learning: 3-Step New-Job Wizard — Validation Layers and Config Round-Trip

**Date:** 2026-04-17
**Commit:** `062846a`

Non-obvious findings from replacing the single-page New Review form with a 3-step wizard.

## Shared dedup sets silently empty role buckets

When exposing `model_router` routes to the UI (`GET /api/config/model-routes`), a shared `seen: set[str]` across the writing and math buckets produced an empty math list. The route tables overlap heavily — `_CLAUDE_ROUTES["writing-self-check"]` and `_CLAUDE_ROUTES["math-reasoning"]` both resolve to `"opus"`; `_GPT_ROUTES[*]` is uniformly `"gpt-5"`. First bucket wins, everything after is deduped away.

**Lesson:** Per-bucket dedup, never shared, when the source data is a many-to-one mapping (role → model). Any future feature that groups by role needs this pattern.

## Reducers can't validate against live async data

Step 2 requires "at least one provider available for the selected mode" — but provider availability is fetched from the backend, not part of wizard state. Putting that check in `GO_NEXT`'s reducer guard means the reducer needs providers as a parameter, which breaks the pure-dispatch model.

**Lesson:** Keep the reducer's advance guard to state-shape invariants only (file present, parser picked). Do the live-data gate at the render layer — `NextButton`'s `disabled` and the blocked-hint text both take `providers` as arguments. The reducer only bounds-checks (`currentStep >= 3 ? noop : currentStep + 1`).

## API request dict round-trip gets "import previous" for free

`ReviewRequest.model_dump()` is stored verbatim as `RunState.config` and exposed via `GET /api/status/{run_id}`. The wizard's `IMPORT_FROM_RUN` action fans that dict back into reducer fields — no replay API, no migration layer. Any new ReviewRequest field (`parser`, `writing_model`, `math_model`) is automatically round-trippable.

**Implication:** Keep `ReviewRequest` as the canonical "job setup" schema. New setup knobs go there first; the wizard and the import-from-previous flow pick them up mechanically. Don't add a parallel "saved preset" store.

## Architecture implications

- **`model_router`'s route tables are UI-exposed now.** `/api/config/model-routes` curates a subset (writing-basic, writing-self-check, math-reasoning) — exposing all 13 task categories as user-facing knobs would be a UX regression. Keep the endpoint curated.
- **Multi-part credentials don't fit `providers.<name>.api_key`.** Mathpix needs `app_id` + `app_key` stored as separate fields in `~/.revisica/config.json`. Any future parser with multi-part auth needs the same treatment.
- **Ollama tab is contract, not stub.** Blocking Next on `backendMode === 'ollama'` is the design — revisiting means adding a real provider class, not flipping a flag.
