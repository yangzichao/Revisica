"""Mutable, thread-safe state for a single job (review or parse).

Extracted from ``api.py`` so on-disk persistence (:mod:`.job_store`) and
crash recovery (:mod:`.recovery`) can share the same shape without
importing the FastAPI app module.
"""

from __future__ import annotations

import logging
import threading
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)

# Keys inside a parse run's result payload that hold the full document body.
# They are dropped from on-disk snapshots — the parsed-documents store
# already owns that data — and rehydrated on demand by ``/api/results``.
HEAVY_RESULT_PAYLOAD_KEYS = ("markdown", "sections")

PersistCallback = Callable[[dict[str, Any]], None]


class RunState:
    """Tracks a single job's progress (review or parse). Thread-safe via internal lock.

    When a ``persist`` callback is supplied, every mutation re-writes the
    run's on-disk snapshot so job history survives a backend restart. The
    callback is invoked outside the internal lock and must never raise into
    the job (persistence failure must not fail the work itself) — it is
    wrapped defensively here regardless.
    """

    def __init__(
        self,
        run_id: str,
        config: dict[str, Any],
        kind: str = "review",
        persist: Optional[PersistCallback] = None,
        retry_of: Optional[str] = None,
        started_at: Optional[str] = None,
    ):
        from datetime import datetime

        self.run_id = run_id
        self.kind = kind
        self.config = config
        self.state = "running"
        self.started_at = started_at or datetime.now().isoformat()
        self.completed_at: Optional[str] = None
        self.run_dir: Optional[str] = None
        self.tasks: list[dict[str, str]] = []
        self.error: Optional[str] = None
        self.retry_of = retry_of
        # Parse jobs stash their manifest here so /api/results can return it
        # without re-reading the on-disk store.
        self.result_payload: Optional[dict[str, Any]] = None
        self._persist_callback = persist
        self._lock = threading.Lock()

    def update(self, **fields: Any) -> None:
        with self._lock:
            for key, value in fields.items():
                setattr(self, key, value)
        self.persist()

    def append_task(self, task: dict[str, str]) -> None:
        with self._lock:
            self.tasks.append(task)
        self.persist()

    def update_task_by_name(
        self,
        name: str,
        status: str,
        detail: Optional[str] = None,
    ) -> None:
        """Update an existing task in place, or append a new one if missing.

        Used by the MinerU chunk progress callback so /api/status returns a
        fine-grained ``[parse, chunk-1/8, chunk-2/8, …]`` task list while a
        large PDF is being split and parsed.
        """
        with self._lock:
            for index, existing in enumerate(self.tasks):
                if existing.get("name") == name:
                    new_task = {**existing, "status": status}
                    if detail is not None:
                        new_task["detail"] = detail
                    self.tasks[index] = new_task
                    break
            else:
                new_task: dict[str, str] = {"name": name, "status": status}
                if detail is not None:
                    new_task["detail"] = detail
                self.tasks.append(new_task)
        self.persist()

    def to_dict(self) -> dict[str, Any]:
        with self._lock:
            return {
                "run_id": self.run_id,
                "kind": self.kind,
                "config": self.config,
                "state": self.state,
                "started_at": self.started_at,
                "completed_at": self.completed_at,
                "run_dir": self.run_dir,
                "tasks": list(self.tasks),
                "error": self.error,
                "retry_of": self.retry_of,
            }

    def snapshot_for_disk(self) -> dict[str, Any]:
        """Return the JSON-serializable snapshot written by the job store.

        Same shape as :meth:`to_dict` plus a *slim* ``result_payload`` —
        heavy document-body keys are dropped because the parsed-documents
        store is the source of truth for them and re-writing a multi-MB
        markdown body on every chunk-progress tick would be wasteful.
        """
        snapshot = self.to_dict()
        with self._lock:
            payload = self.result_payload
        if payload is not None:
            snapshot["result_payload"] = {
                key: value
                for key, value in payload.items()
                if key not in HEAVY_RESULT_PAYLOAD_KEYS
            }
        return snapshot

    def persist(self) -> None:
        """Write the current snapshot through the persist callback, if any."""
        if self._persist_callback is None:
            return
        try:
            self._persist_callback(self.snapshot_for_disk())
        except Exception as error:
            logger.warning(
                "Failed to persist run %s snapshot: %s", self.run_id, error
            )

    @classmethod
    def from_snapshot(
        cls,
        snapshot: dict[str, Any],
        persist: Optional[PersistCallback] = None,
    ) -> "RunState":
        """Rebuild a RunState from an on-disk snapshot (see :mod:`.job_store`)."""
        run_state = cls(
            run_id=str(snapshot.get("run_id") or ""),
            config=dict(snapshot.get("config") or {}),
            kind=str(snapshot.get("kind") or "review"),
            persist=persist,
            retry_of=snapshot.get("retry_of"),
            started_at=snapshot.get("started_at"),
        )
        run_state.state = str(snapshot.get("state") or "running")
        run_state.completed_at = snapshot.get("completed_at")
        run_state.run_dir = snapshot.get("run_dir")
        run_state.tasks = [dict(task) for task in (snapshot.get("tasks") or [])]
        run_state.error = snapshot.get("error")
        payload = snapshot.get("result_payload")
        run_state.result_payload = dict(payload) if payload else None
        return run_state
