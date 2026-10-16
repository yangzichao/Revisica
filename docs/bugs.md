# Bugs & Cleanup

**Filed:** 2026-04-11
**Last verified:** 2026-10-15 (commit `a0dbe05`)

## Open

None as of 2026-10-15.

## Fixed

### 1. `.gitignore` stale paths after benchmark rename — FIXED

**Commit:** `681da94` → fixed in this session
**Was:** 4 dead `.gitignore` rules pointing to old `*_cases` paths
**Fix:** Updated to `benchmarks/math/runs/`, `benchmarks/writing/runs/`, etc.

### 3. `agents/codex/` missing 2 agent definitions — FIXED

**Commit:** this session
**Was:** `refine-eval-judge.md` and `writing-self-checker.md` missing from Codex agents
**Fix:** Created both files with content matching the Claude JSON equivalents.

### 2. Three redundant agent definition locations — FIXED

**Fixed:** 2026-10-15
**Was:** Codex CLI read its system prompt from `agents/codex/*.md`, which had drifted far from `src/revisica/agents/definitions/*.py` (difflib similarity 0.20 for `math-proof-reviewer`), and versioned agents (`math-proof-reviewer-vN`) had no `.md` at all, so Codex ran them without a system prompt. `agents/` sat outside the package, so the frozen DMG had neither the prompts nor `findings.schema.json`. Claude CLI separately sent `{"instructions": ...}` to `--agents`; Claude Code 2.1.301 rejects that with `Invalid --agents configuration` (it requires `description` + `prompt`).
**Fix:** `AgentSpec` now carries `system_prompt` / `description` / `tools`, and all four providers read them. `agents/claude/` and `agents/codex/` are deleted; the schema moved to `src/revisica/agents/output_schemas/` (shipped as package data). Benchmark provenance now hashes the Python proof-agent modules, so `math_proof_review` hashes differ from older registry rows.

### 4. Silent exception swallowing — no logging on failure — FIXED

**Commit:** session 2 (2026-04-11)
**Was:** 5 bare `except Exception:` blocks with no logging.
**Fix:** Added `logging.warning()` with `exc_info=True` to all 5 locations. JSON parse fallback uses `logging.debug()` (high-frequency, noise reduction).

### 5. `review.py` `_run_provider()` takes unused `platform` parameter — FIXED

**Commit:** `9cdf0ef` (P0.5)
**Was:** `platform: PlatformStatus` parameter accepted but ignored in `_run_provider()` and `_run_provider_agent()`.
**Fix:** Removed dead parameter and updated all call sites.

### 6. Claude CLI runs load the operator's CLAUDE.md and auto-memory — FIXED

**Fixed:** 2026-10-15
**Was:** `claude -p` loads `~/.claude/CLAUDE.md`, any `CLAUDE.md` in the working directory, and the project's auto-memory `MEMORY.md`, on top of the `--agents` prompt. On a machine whose `CLAUDE.md` says "reply in mixed Chinese + English", an English paper's polish report and writing final report came back in Chinese. Benchmark runs inherit the same instructions, so results depend on whose machine ran them.
**Fix:** `providers/cli_claude.py` sets `CLAUDE_CODE_DISABLE_CLAUDE_MDS=1` and `CLAUDE_CODE_DISABLE_AUTO_MEMORY=1` for every Claude CLI subprocess. Probed with Claude Code 2.1.301: with both set, the model sees none of those files. Settings files still load, so OAuth, `apiKeyHelper` and proxy config keep working (`--setting-sources` or `--bare` would have dropped them).

### 7. Codex CLI runs load the operator's `~/.codex/AGENTS.md` — FIXED

**Fixed:** 2026-10-15 (`16c9244`, codex-cli 0.162.0-alpha.17.2)
**Was:** Same class as #6. `codex exec` puts `$CODEX_HOME/AGENTS.md` in front of Revisica's prompt. Neither `-c project_doc_max_bytes=0` nor `-c instructions=""` stops it. Asked for the headings of any AGENTS.md instructions, a Revisica Codex run listed `# Coding style preferences` and three more. Codex memories also carried past sessions into later runs.
**Fix:** `providers/codex_home.py` runs Codex with `CODEX_HOME=~/.revisica/codex-home`, which symlinks the user's `auth.json` and `config.toml` and has no `AGENTS.md`. Codex writes `auth.json` through the symlink (checked with `codex login --with-api-key` on a dummy file), so token refreshes reach the user's login. Keyring credentials, or no `auth.json` and no API key env var, keep the user's home. Runs pass `-c features.memories=false`. Same probe after the fix: `NONE`.

## Confirmed-bug sweep (2026-10-15, branch `fix/confirmed-bug-sweep`)

### 8. CLI rate-limit retry fired on prompt text and on timeouts — FIXED

**Fixed:** `19429d2`
**Was:** Both CLI providers retried any failed run whose stderr contained "rate" or "overloaded", 20 times with 10-minute sleeps. `codex exec` echoes the prompt into stderr, and prompts contain "accurate" and "strategy", so an invalid model name took ~3.3 hours per call. Timeouts were retried too (~6.8 hours at `--timeout-seconds 600`). Timeout stderr showed up as a `b'...'` repr, and the Codex stdout fallback never ran.
**Fix:** `providers/rate_limit_retry.py` reads only the CLI's error text (Codex `ERROR:` lines; Claude stdout/stderr) and matches real rate-limit messages. Timeouts return after one attempt. Invalid model on real Codex: 1 attempt, 3.0s.

### 9. Writing judge and unified summary misreported the writing lane — FIXED

**Fixed:** `72d68a0`
**Was:** The judge read role JSON files written before self-check, so filtered findings still reached `final_report.md`. Two reviewers with the same `provider:model` overwrote each other's files. When every role failed, no `final_report.md` was written. The unified summary dropped lane warnings and always said "Writing: completed".
**Fix:** Role files are rewritten after self-check. Stems are allocated at submit time (`basic_claude_sonnet_2`). An all-failed run writes a failed report listing each role's error. Lane warnings carry up with a `Writing:`/`Math:` prefix, and the status says failed when no role produced output.

### 10. API backend mode could not run reviews — FIXED

**Fixed:** `d1e7554`
**Was:** Reviewer availability only looked for the `codex`/`claude` binaries. With `REVISICA_BACKEND_MODE=api` and a key, `revisica review` failed with "No supported provider detected", and `--reviewer-a anthropic-api:...` raised `KeyError`. The provider registry also kept the mode the process started with.
**Fix:** `providers/availability.py` maps each name to a runnable provider for the current mode. The writing lane, math lane and polish use it. The registry is rebuilt when the mode changes.

### 11. Math lane lost claims on ingested Markdown — FIXED

**Fixed:** `2c20c34`
**Was:** Integral and inequality claims were only read from `\[ ... \]`. Pandoc, tex-basic and MinerU write `$$ ... $$`, so `examples/minimal_paper.tex` went from 3 refuted claims to 2. With MinerU spacing (`g (x) = \frac {1}{x - 1}`), `g` was dropped and its continuity claim bound to `f = x^2`, then came out machine-verified.
**Fix:** Both display forms are matched, `normalize_latex` closes parser spacing, and a continuity claim is skipped when the nearest definition did not parse. All four ingestion paths refute the same 3 claims.

### 12. LLM proof review cited line numbers of a different file — FIXED

**Fixed:** `50e869a`
**Was:** Proof blueprints came from the ingested Markdown, but the review tasks pointed agents at the original file ("Theorem line: 2" for a theorem on line 9 of the .tex; a PDF for PDF input).
**Fix:** The ingested text is written to `math/<stem>.normalized.md` and the tasks point there.

### 13. Desktop reviews were written inside the app bundle; run dirs could collide — FIXED

**Fixed:** `2c116b7`, test `b9fe51b`
**Was:** Runs without an output dir went to `<cwd>/reviews`, and the desktop backend's cwd is the bundle's Resources dir. Run dirs were named to the second, so two runs of one paper in the same second shared a directory.
**Fix:** `REVISICA_REVIEWS_DIR` sets the root; the desktop app sets `<userData>/reviews`. `create_review_run_dir()` adds `-2`, `-3` on collision.

### 14. API `custom_instructions` never reached the polish agent — FIXED

**Fixed:** `5f27a9c`
**Was:** `POST /api/review` accepted `custom_instructions`, but `_execute_review` did not forward it.
**Fix:** `review_unified` takes it and puts it on the `ReviewConfig` (polish mode only).

### 15. Config endpoints saved env-only API keys to disk — FIXED

**Fixed:** `1265007`
**Was:** The settings endpoints saved the env-merged config, so any settings change wrote `ANTHROPIC_API_KEY` / `OPENAI_API_KEY` / `MATHPIX_API_KEY` and `REVISICA_BACKEND_MODE` into `~/.revisica/config.json` in plain text.
**Fix:** They start from `load_saved_config()`, the file as saved.

### 16. Desktop jobs finished "completed" when the review produced nothing — FIXED

**Fixed:** `a0dbe05`
**Was:** `_execute_review` marked a job completed whenever `review_unified` returned. With every agent failing, review and polish jobs both ended completed with no error. The desktop showed an empty review, or a polish report reading "No polish suggestions generated.", and offered no Retry.
**Fix:** `UnifiedReviewRun.failure` is set when no writing role produced usable output or the polish agent did not run. The job is then marked failed with that reason and the first role errors.
