"""Job persistence + crash recovery + run-management endpoints.

The desktop app restarts the Python backend on every app launch, so job
state must round-trip through ``~/.revisica/jobs`` (here isolated via
``REVISICA_JOBS_DIR``). Coverage:

  1. **Store round-trip.** Snapshots write atomically, reload, and delete;
     heavy parse payload keys (markdown/sections) never hit disk.
  2. **Recovery semantics.** running → failed("interrupted"), queued parse
     → re-enqueued, finished runs restored verbatim, corrupt files skipped.
  3. **HTTP surface.** /api/runs lists newest-first; retry relaunches a
     failed run with its original config and records ``retry_of``; delete
     refuses in-flight runs and removes finished ones from memory + disk.
"""

from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

import revisica.api as api
from revisica.jobs import (
    INTERRUPTED_ERROR_MESSAGE,
    RunState,
    get_run,
    list_run_snapshots,
    persist_run_snapshot,
    recover_runs_from_disk,
    register_run,
    reset_registry_for_tests,
)
from revisica.jobs.job_store import (
    delete_run_snapshot,
    jobs_root,
    load_all_run_snapshots,
)

_FAKE_TOKEN = "test-token-for-job-endpoints"
_AUTH_HEADERS = {"Authorization": f"Bearer {_FAKE_TOKEN}"}


@pytest.fixture(autouse=True)
def isolated_jobs_environment(monkeypatch, tmp_path):
    """Point the job store at a temp dir and start from an empty registry."""
    monkeypatch.setenv("REVISICA_JOBS_DIR", str(tmp_path / "jobs"))
    reset_registry_for_tests()
    yield
    reset_registry_for_tests()


@pytest.fixture
def api_client(monkeypatch):
    monkeypatch.setattr(api, "_API_TOKEN", _FAKE_TOKEN)
    return TestClient(api.app)


@pytest.fixture
def stubbed_parse_queue(monkeypatch):
    """Capture parse submissions instead of running the real worker thread."""
    submitted: list[tuple[str, object]] = []

    class RecordingQueue:
        def put(self, item):
            submitted.append(item)

    monkeypatch.setattr(api, "_parse_queue", RecordingQueue())
    monkeypatch.setattr(api, "_ensure_parse_worker_started", lambda: None)
    return submitted


def _persisted_run(
    run_id: str,
    state: str,
    kind: str = "parse",
    config: dict | None = None,
    started_at: str = "2026-06-10T10:00:00",
    tasks: list | None = None,
) -> RunState:
    """Build a RunState wired to the on-disk store, in the given state."""
    run_state = RunState(
        run_id,
        config if config is not None else {"file_path": "/tmp/paper.pdf"},
        kind=kind,
        persist=persist_run_snapshot,
        started_at=started_at,
    )
    if tasks:
        for task in tasks:
            run_state.append_task(task)
    run_state.update(state=state)
    return run_state


# ── job store ───────────────────────────────────────────────────────


class TestJobStore:
    def test_snapshot_round_trips(self):
        run_state = _persisted_run("run-aaa", "completed")
        loaded = load_all_run_snapshots()
        assert [row["run_id"] for row in loaded] == ["run-aaa"]
        assert loaded[0]["state"] == "completed"
        assert loaded[0]["config"] == run_state.config

    def test_every_mutation_rewrites_the_snapshot(self):
        run_state = _persisted_run("run-bbb", "running")
        run_state.update_task_by_name("chunk-1", "running", detail="1/3")
        snapshot = load_all_run_snapshots()[0]
        assert snapshot["tasks"][-1] == {
            "name": "chunk-1",
            "status": "running",
            "detail": "1/3",
        }

    def test_heavy_parse_payload_keys_stay_off_disk(self):
        run_state = _persisted_run("run-ccc", "running")
        run_state.result_payload = {
            "id": "paper-mineru-20260610",
            "title": "A Paper",
            "section_count": 4,
            "markdown": "# huge body " * 1000,
            "sections": [{"id": "s1", "content": "..."}],
        }
        run_state.update(state="completed")
        snapshot = load_all_run_snapshots()[0]
        assert snapshot["result_payload"]["id"] == "paper-mineru-20260610"
        assert snapshot["result_payload"]["section_count"] == 4
        assert "markdown" not in snapshot["result_payload"]
        assert "sections" not in snapshot["result_payload"]

    def test_delete_removes_the_file(self):
        _persisted_run("run-ddd", "failed")
        delete_run_snapshot("run-ddd")
        assert load_all_run_snapshots() == []

    def test_corrupt_snapshot_is_skipped(self):
        _persisted_run("run-good", "completed")
        (jobs_root() / "run-bad.json").write_text("{not json", encoding="utf-8")
        loaded = load_all_run_snapshots()
        assert [row["run_id"] for row in loaded] == ["run-good"]


# ── recovery ────────────────────────────────────────────────────────


class TestRecovery:
    def test_running_run_is_marked_interrupted(self):
        _persisted_run(
            "run-mid-flight",
            "running",
            tasks=[
                {"name": "parse", "status": "running"},
                {"name": "chunk-p0001-p0040", "status": "cached"},
            ],
        )
        reset_registry_for_tests()  # simulate process restart

        restored = recover_runs_from_disk(resubmit_parse=lambda rs: None)

        assert restored == 1
        recovered = get_run("run-mid-flight")
        assert recovered.state == "failed"
        assert recovered.error == INTERRUPTED_ERROR_MESSAGE
        task_status = {task["name"]: task["status"] for task in recovered.tasks}
        assert task_status["parse"] == "failed"
        # Finished chunk work is kept so the UI shows what was already done.
        assert task_status["chunk-p0001-p0040"] == "cached"

    def test_queued_parse_is_resubmitted(self):
        _persisted_run("run-queued", "queued")
        reset_registry_for_tests()

        resubmitted: list[str] = []
        recover_runs_from_disk(
            resubmit_parse=lambda rs: resubmitted.append(rs.run_id)
        )

        assert resubmitted == ["run-queued"]
        assert get_run("run-queued").state == "queued"

    def test_finished_runs_are_restored_verbatim(self):
        _persisted_run("run-done", "completed", kind="review")
        reset_registry_for_tests()

        recover_runs_from_disk(resubmit_parse=lambda rs: None)

        recovered = get_run("run-done")
        assert recovered.state == "completed"
        assert recovered.kind == "review"

    def test_failed_resubmission_marks_run_interrupted(self):
        _persisted_run("run-queued", "queued")
        reset_registry_for_tests()

        def explode(run_state):
            raise RuntimeError("queue is gone")

        recover_runs_from_disk(resubmit_parse=explode)
        assert get_run("run-queued").state == "failed"


# ── HTTP endpoints ──────────────────────────────────────────────────


class TestRunsEndpoints:
    def test_runs_listing_requires_auth(self, api_client):
        assert api_client.get("/api/runs").status_code == 401

    def test_runs_listing_is_newest_first(self, api_client):
        register_run(_persisted_run("run-old", "completed", started_at="2026-06-10T09:00:00"))
        register_run(_persisted_run("run-new", "failed", started_at="2026-06-10T11:00:00"))

        response = api_client.get("/api/runs", headers=_AUTH_HEADERS)
        assert response.status_code == 200
        run_ids = [row["run_id"] for row in response.json()["runs"]]
        assert run_ids == ["run-new", "run-old"]

    def test_retry_unknown_run_is_404(self, api_client):
        response = api_client.post(
            "/api/runs/nope/retry", headers=_AUTH_HEADERS
        )
        assert response.status_code == 404

    def test_retry_refuses_non_failed_runs(self, api_client):
        register_run(_persisted_run("run-busy", "running"))
        response = api_client.post(
            "/api/runs/run-busy/retry", headers=_AUTH_HEADERS
        )
        assert response.status_code == 409

    def test_retry_resubmits_failed_parse_with_original_config(
        self, api_client, stubbed_parse_queue,
    ):
        config = {
            "file_path": "/tmp/big-paper.pdf",
            "parser": "mineru",
            "mineru_backend": "vlm",
        }
        register_run(_persisted_run("run-broken", "failed", config=config))

        response = api_client.post(
            "/api/runs/run-broken/retry", headers=_AUTH_HEADERS
        )

        assert response.status_code == 200
        body = response.json()
        assert body["retry_of"] == "run-broken"
        assert body["status"] == "queued"

        new_run = get_run(body["run_id"])
        assert new_run.retry_of == "run-broken"
        assert new_run.config == config
        assert [run_id for run_id, _ in stubbed_parse_queue] == [body["run_id"]]

    def test_delete_refuses_in_flight_runs(self, api_client):
        register_run(_persisted_run("run-live", "queued"))
        response = api_client.delete(
            "/api/runs/run-live", headers=_AUTH_HEADERS
        )
        assert response.status_code == 409

    def test_delete_removes_run_from_memory_and_disk(self, api_client):
        register_run(_persisted_run("run-gone", "failed"))
        response = api_client.delete(
            "/api/runs/run-gone", headers=_AUTH_HEADERS
        )
        assert response.status_code == 200
        assert get_run("run-gone") is None
        assert load_all_run_snapshots() == []


class TestRestartEndToEnd:
    def test_lifespan_restores_history_and_requeues_parses(
        self, api_client, stubbed_parse_queue,
    ):
        _persisted_run("run-finished", "completed", started_at="2026-06-10T09:00:00")
        _persisted_run("run-crashed", "running", started_at="2026-06-10T10:00:00")
        _persisted_run("run-waiting", "queued", started_at="2026-06-10T11:00:00")
        reset_registry_for_tests()  # simulate the backend process dying

        # Entering the client context runs the FastAPI lifespan → recovery.
        with api_client as client:
            response = client.get("/api/runs", headers=_AUTH_HEADERS)

        rows = {row["run_id"]: row for row in response.json()["runs"]}
        assert rows["run-finished"]["state"] == "completed"
        assert rows["run-crashed"]["state"] == "failed"
        assert "Interrupted" in rows["run-crashed"]["error"]
        assert rows["run-waiting"]["state"] == "queued"
        assert [run_id for run_id, _ in stubbed_parse_queue] == ["run-waiting"]


def test_registry_snapshot_listing_matches_registered_runs():
    register_run(_persisted_run("run-1", "completed", started_at="2026-06-10T08:00:00"))
    register_run(_persisted_run("run-2", "running", started_at="2026-06-10T09:00:00"))
    listed = [row["run_id"] for row in list_run_snapshots()]
    assert listed == ["run-2", "run-1"]
