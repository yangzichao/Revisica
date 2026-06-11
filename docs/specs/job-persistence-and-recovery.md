# Job Persistence and Crash Recovery

## Status

Implemented (2026-06-10).

## Problem

The desktop app starts and stops the Python backend with the app itself, and
all job state lived in an in-memory `OrderedDict` inside `api.py`. Every app
relaunch therefore:

- wiped the Jobs page history (the renderer kept run ids in
  `localStorage` and polled `/api/status/{id}` per id — after a restart each
  poll 404'd and was silently skipped);
- silently dropped parse jobs that were still queued for the single MinerU
  worker;
- left no way to relaunch a failed run other than re-filling the New Job /
  Parse forms, even though the MinerU chunk cache makes a parse retry nearly
  free.

The per-id polling loop was also O(N) HTTP requests every 2 seconds.

## Design

New `src/revisica/jobs/` subpackage:

| Module | Role |
|---|---|
| `run_state.py` | `RunState` (moved out of `api.py`) + optional persist callback fired after every mutation; `retry_of` field; `from_snapshot` rehydration |
| `job_store.py` | One JSON file per run at `~/.revisica/jobs/<run_id>.json` (override: `REVISICA_JOBS_DIR`); atomic write via temp file + `os.replace`; log-and-swallow on failure — persistence must never fail the job |
| `registry.py` | In-memory `OrderedDict` registry; eviction past 100 runs also deletes the on-disk snapshot so the jobs dir cannot grow unbounded |
| `recovery.py` | Startup recovery: completed/failed restored verbatim; **queued parses re-enqueued** (explicitly requested, never started); **running runs marked failed** with an "interrupted by backend restart" error (no in-place resume path exists; retry relaunches them) |

Snapshots are *slim*: a parse run's `result_payload` is persisted without
`markdown`/`sections` (the parsed-documents store owns those);
`/api/results/{id}` rehydrates them from `load_parsed_document` when a
restored run is queried.

API surface added to `api.py` (recovery runs in the FastAPI lifespan):

- `GET /api/runs` — all runs, newest first; replaces client-side run-id
  bookkeeping and collapses the Jobs page polling to one request.
- `POST /api/runs/{run_id}/retry` — relaunch a **failed** run with its
  original config; response and new run carry `retry_of`. 409 otherwise.
- `DELETE /api/runs/{run_id}` — remove a finished run from memory + disk;
  409 for running/queued runs.

Renderer (`Jobs.tsx`): job list now polls `/api/runs`; rows show a source
label (file basename or parsed-document id) and a hover trash button with
the same two-click confirm used in Library (`useDeleteConfirm`); failed job
detail shows a **Retry job** button that navigates to the new run; runs
created by retry link back to the original. The `revisica_run_ids`
localStorage mechanism was removed from `Jobs.tsx`, `ParsePage.tsx`, and
`NewJobWizard.tsx`.

## Implementation plan

Done in one pass: subpackage → `api.py` rewiring → pytest coverage
(`tests/test_job_persistence.py`, 18 tests: store round-trip, slim
payloads, recovery semantics, endpoint auth/409/404 behavior, lifespan
end-to-end restart) → renderer changes → live verification (real server
kill/restart cycles + Playwright against the dev renderer).

## Acceptance criteria

- [x] Job history survives a backend restart (verified by killing and
      restarting `revisica serve` with seeded snapshots).
- [x] A parse queued at crash time runs to completion automatically after
      restart.
- [x] A run that was mid-flight at crash time shows as failed with an
      "interrupted" explanation; finished chunk tasks (e.g. `cached`) are
      preserved in its task list.
- [x] Retry of a failed run reuses the original config, records `retry_of`,
      and completes; retried MinerU parses hit the chunk cache.
- [x] Restored completed parses still return full markdown via
      `/api/results` (rehydrated from the parsed-documents store).
- [x] Deleting a finished run removes it from the list and from disk;
      in-flight runs cannot be deleted or retried.
- [x] `pytest` (111 passed), `tsc --noEmit`, and `electron-vite build` all
      green; `benchmark-run --suite math-cases --mode deterministic-only`
      unaffected.
