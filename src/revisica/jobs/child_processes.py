"""Stop the backend's child processes when the API server shuts down.

The desktop app quits by sending SIGTERM to the backend's pid. Claude and
Codex CLI runs (and MinerU parses) the backend had started kept running,
reparented to launchd, until they finished on their own: with a fake
``claude`` that sleeps, all 9 role runs of a review outlived the backend.
Real ones keep spending the user's quota on a review nobody will read.

The processes are found in the process table instead of being registered
where they start, so every ``subprocess.run`` call site stays as it is.
The whole tree is stopped, not only direct children: a CLI's own tool
processes would otherwise be reparented when the CLI exits. CLI use needs
none of this: Ctrl-C reaches the whole foreground process group.
"""

from __future__ import annotations

import logging
import os
import signal
import subprocess
import sys
import time

_logger = logging.getLogger(__name__)

POLL_INTERVAL_SECONDS = 0.1


def terminate_child_processes(parent_pid: int | None = None, grace_seconds: float = 3.0) -> list[int]:
    """SIGTERM every descendant of ``parent_pid``; SIGKILL those left after the grace period.

    Descendants that appear during the grace period are stopped too: a
    lane whose agent was stopped moves straight on to its next agent. So
    this returns only after two scans in a row found nothing running, or
    at the deadline. Returns the pids that were signalled.
    """
    if sys.platform == "win32":
        return []
    parent_pid = os.getpid() if parent_pid is None else parent_pid
    signalled_pids: list[int] = []
    deadline = time.monotonic() + grace_seconds
    quiet_scans = 0
    while quiet_scans < 2 and time.monotonic() < deadline:
        new_pids = [pid for pid in descendant_pids(parent_pid) if pid not in signalled_pids]
        for pid in new_pids:
            _send_signal(pid, signal.SIGTERM)
        signalled_pids.extend(new_pids)
        if new_pids or any(_is_alive(pid) for pid in signalled_pids):
            quiet_scans = 0
        else:
            quiet_scans += 1
        time.sleep(POLL_INTERVAL_SECONDS)
    # A grandchild whose parent exited is no longer in the tree, so the
    # signalled pids are killed directly. Pids are handed out in sequence,
    # so one reused by an unrelated process within the grace period is not
    # a practical risk.
    for pid in signalled_pids:
        if _is_alive(pid):
            _send_signal(pid, signal.SIGKILL)
    return signalled_pids


def descendant_pids(parent_pid: int) -> list[int]:
    children_by_parent: dict[int, list[int]] = {}
    for pid, ppid in _process_table():
        children_by_parent.setdefault(ppid, []).append(pid)
    descendants: list[int] = []
    pending = [parent_pid]
    while pending:
        for child_pid in children_by_parent.get(pending.pop(), []):
            if child_pid not in descendants:
                descendants.append(child_pid)
                pending.append(child_pid)
    return descendants


def _process_table() -> list[tuple[int, int]]:
    """``(pid, parent pid)`` for every process, from ``ps``."""
    try:
        with subprocess.Popen(
            ["ps", "-A", "-o", "pid=", "-o", "ppid="],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
        ) as ps_process:
            stdout, _ = ps_process.communicate(timeout=5)
    except (OSError, subprocess.TimeoutExpired):
        _logger.warning("Could not list processes to stop the backend's children", exc_info=True)
        return []
    table: list[tuple[int, int]] = []
    for line in stdout.splitlines():
        fields = line.split()
        if len(fields) == 2 and fields[0].isdigit() and fields[1].isdigit():
            pid = int(fields[0])
            # ps lists itself, as a child of this process.
            if pid != ps_process.pid:
                table.append((pid, int(fields[1])))
    return table


def _is_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _send_signal(pid: int, signal_number: int) -> None:
    try:
        os.kill(pid, signal_number)
    except ProcessLookupError:
        pass
    except PermissionError:
        _logger.warning("Not allowed to signal child process %s", pid)
