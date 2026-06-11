"""Job tracking: run state, on-disk persistence, registry, crash recovery."""

from .job_store import (
    JOBS_DIR_ENV_VAR,
    delete_run_snapshot,
    jobs_root,
    load_all_run_snapshots,
    persist_run_snapshot,
)
from .recovery import INTERRUPTED_ERROR_MESSAGE, recover_runs_from_disk
from .registry import (
    MAX_RETAINED_RUNS,
    get_run,
    list_run_snapshots,
    register_run,
    remove_run,
    reset_registry_for_tests,
)
from .run_state import RunState

__all__ = [
    "JOBS_DIR_ENV_VAR",
    "INTERRUPTED_ERROR_MESSAGE",
    "MAX_RETAINED_RUNS",
    "RunState",
    "delete_run_snapshot",
    "get_run",
    "jobs_root",
    "list_run_snapshots",
    "load_all_run_snapshots",
    "persist_run_snapshot",
    "recover_runs_from_disk",
    "register_run",
    "remove_run",
    "reset_registry_for_tests",
]
