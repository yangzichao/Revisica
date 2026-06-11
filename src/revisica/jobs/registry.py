"""In-memory registry of live :class:`RunState` objects.

The registry is the single source of truth while the server runs; the job
store (:mod:`.job_store`) mirrors it to disk so history survives restarts.
Eviction keeps both sides in sync — when an old finished run falls off the
in-memory cap, its on-disk snapshot is deleted too, so the jobs directory
cannot grow without bound.
"""

from __future__ import annotations

import threading
from collections import OrderedDict
from typing import Any, Optional

from .job_store import delete_run_snapshot
from .run_state import RunState

# Cap retained runs so a long-lived server cannot grow the registry (or the
# on-disk jobs directory) without bound.
MAX_RETAINED_RUNS = 100

_runs: "OrderedDict[str, RunState]" = OrderedDict()
_runs_lock = threading.Lock()


def register_run(run_state: RunState) -> None:
    """Add a run to the registry, evicting the oldest finished runs past the cap."""
    evicted_run_ids: list[str] = []
    with _runs_lock:
        _runs[run_state.run_id] = run_state
        while len(_runs) > MAX_RETAINED_RUNS:
            # Safe: we `break` immediately after the single `pop`, so we never
            # continue iterating a mutated dict within the same `for` pass.
            for run_id, state in _runs.items():
                if state.state in ("completed", "failed"):
                    _runs.pop(run_id)
                    evicted_run_ids.append(run_id)
                    break
            else:
                break
    run_state.persist()
    for run_id in evicted_run_ids:
        delete_run_snapshot(run_id)


def get_run(run_id: str) -> Optional[RunState]:
    with _runs_lock:
        return _runs.get(run_id)


def list_run_snapshots() -> list[dict[str, Any]]:
    """Return every registered run as a dict, newest ``started_at`` first."""
    with _runs_lock:
        run_states = list(_runs.values())
    snapshots = [run_state.to_dict() for run_state in run_states]
    snapshots.sort(key=lambda row: row.get("started_at") or "", reverse=True)
    return snapshots


def remove_run(run_id: str) -> Optional[RunState]:
    """Drop a run from the registry and delete its on-disk snapshot."""
    with _runs_lock:
        run_state = _runs.pop(run_id, None)
    if run_state is not None:
        delete_run_snapshot(run_id)
    return run_state


def reset_registry_for_tests() -> None:
    """Clear the registry without touching disk (test isolation only)."""
    with _runs_lock:
        _runs.clear()
