"""The API server stops its child processes when it shuts down.

Before: the desktop app's SIGTERM ended the backend, but every Claude CLI
run of the review in flight kept going, reparented to launchd (probed with
a fake ``claude`` that sleeps: 9 of 9 outlived the backend), and the job
was recorded as failed with "exit -15" from every agent.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import textwrap
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import revisica.api as api
from revisica.jobs import job_store
from revisica.jobs.child_processes import descendant_pids, terminate_child_processes

pytestmark = pytest.mark.skipif(sys.platform == "win32", reason="POSIX process tree")

# Stands in for the backend: starts a CLI-like child, one with its own
# grandchild, and one that ignores SIGTERM, then reaps them like
# subprocess.run would.
_FAKE_BACKEND = textwrap.dedent(
    """
    import subprocess, sys, time
    children = [
        subprocess.Popen(["sleep", "30"]),
        subprocess.Popen(["sh", "-c", "sleep 30; true"]),
        subprocess.Popen(["sh", "-c", "trap '' TERM; sleep 30; true"]),
    ]
    print("started", flush=True)
    for child in children:
        child.wait()
    time.sleep(30)
    """
)


@pytest.fixture
def fake_backend():
    process = subprocess.Popen([sys.executable, "-c", _FAKE_BACKEND], stdout=subprocess.PIPE, text=True)
    assert process.stdout.readline().strip() == "started"
    yield process
    process.kill()
    process.wait()


def wait_for_tree(parent_pid: int, expected_size: int) -> list[int]:
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        pids = descendant_pids(parent_pid)
        if len(pids) >= expected_size:
            return pids
        time.sleep(0.05)
    raise AssertionError(f"expected {expected_size} descendants, saw {descendant_pids(parent_pid)}")


def is_running(pid: int) -> bool:
    state = subprocess.run(["ps", "-o", "stat=", "-p", str(pid)], capture_output=True, text=True).stdout.strip()
    return bool(state) and not state.startswith("Z")


def test_the_whole_tree_is_stopped_including_grandchildren(fake_backend: subprocess.Popen) -> None:
    # 3 children plus 2 grandchildren (the sleeps under each sh).
    tree = wait_for_tree(fake_backend.pid, expected_size=5)

    signalled = terminate_child_processes(parent_pid=fake_backend.pid, grace_seconds=1)

    assert set(tree) <= set(signalled)
    time.sleep(0.2)
    assert [pid for pid in tree if is_running(pid)] == []
    assert fake_backend.poll() is None


def test_nothing_to_stop_returns_quickly() -> None:
    lone_process = subprocess.Popen(["sleep", "30"])
    try:
        started = time.monotonic()
        assert terminate_child_processes(parent_pid=lone_process.pid) == []
        assert time.monotonic() - started < 1
    finally:
        lone_process.kill()
        lone_process.wait()


def test_shutdown_stops_children_and_leaves_running_jobs_to_recovery(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("REVISICA_JOBS_DIR", str(tmp_path / "jobs"))
    terminate_calls: list[int] = []
    monkeypatch.setattr(api, "terminate_child_processes", lambda: terminate_calls.append(os.getpid()))

    try:
        with TestClient(api.app):
            job_store.persist_run_snapshot({"run_id": "in-flight", "state": "running"})
        job_store.persist_run_snapshot({"run_id": "in-flight", "state": "failed", "error": "exit -15"})

        assert terminate_calls == [os.getpid()]
        saved = json.loads((tmp_path / "jobs" / "in-flight.json").read_text(encoding="utf-8"))
        assert saved["state"] == "running"
    finally:
        job_store.resume_snapshot_writes()
