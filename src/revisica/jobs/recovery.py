"""Startup recovery: rebuild job history from disk after a backend restart.

The desktop app starts and stops the Python backend with the app itself, so
every app relaunch is a "server crash" from the job registry's point of
view. Recovery restores the picture the user last saw:

- **completed / failed** runs come back exactly as they were, so the Jobs
  page keeps its history.
- **queued** parse runs were accepted but never started — they are
  re-enqueued automatically, preserving the user's explicit request.
- **running** runs were cut off mid-flight. Their work cannot be resumed
  in-place, so they are marked failed with an "interrupted" error; the
  retry endpoint relaunches them (parses resume cheaply from cached
  MinerU chunks).
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Callable

from .job_store import load_all_run_snapshots, persist_run_snapshot
from .registry import register_run
from .run_state import RunState

logger = logging.getLogger(__name__)

INTERRUPTED_ERROR_MESSAGE = (
    "Interrupted: the Revisica backend restarted while this job was in "
    "flight. Retry to run it again — parses resume from cached chunks."
)

# Task statuses that mean "still doing work" at the moment of the crash.
_IN_FLIGHT_TASK_STATUSES = ("pending", "running", "fallback")

ResubmitParse = Callable[[RunState], None]


def recover_runs_from_disk(resubmit_parse: ResubmitParse) -> int:
    """Load persisted runs into the registry. Returns the number restored.

    ``resubmit_parse`` is called for each queued parse run, after it has
    been registered, so the caller can push it back onto the parse queue.
    Snapshots are registered oldest-first so registry eviction keeps the
    newest runs when there are more than the retention cap.
    """
    restored = 0
    for snapshot in load_all_run_snapshots():
        run_state = RunState.from_snapshot(snapshot, persist=persist_run_snapshot)

        if run_state.state == "running":
            _mark_interrupted(run_state)
            register_run(run_state)
        elif run_state.state == "queued":
            if run_state.kind == "parse":
                register_run(run_state)
                try:
                    resubmit_parse(run_state)
                except Exception as error:
                    logger.warning(
                        "Failed to re-enqueue parse run %s: %s",
                        run_state.run_id,
                        error,
                    )
                    _mark_interrupted(run_state)
            else:
                # Reviews never sit in "queued" today; treat any stray one
                # like an interrupted run rather than inventing a resume path.
                _mark_interrupted(run_state)
                register_run(run_state)
        else:
            register_run(run_state)
        restored += 1

    return restored


def _mark_interrupted(run_state: RunState) -> None:
    """Flip an in-flight run to failed with a clear restart explanation."""
    for task in list(run_state.tasks):
        if task.get("status") in _IN_FLIGHT_TASK_STATUSES:
            run_state.update_task_by_name(
                str(task.get("name") or ""),
                "failed",
                detail="interrupted by backend restart",
            )
    run_state.update(
        state="failed",
        error=INTERRUPTED_ERROR_MESSAGE,
        completed_at=datetime.now().isoformat(),
    )
