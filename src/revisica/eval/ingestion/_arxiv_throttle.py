"""Shared arxiv request throttle.

Both the PDF downloader (``corpus.py``) and the ground-truth fetcher
(``ground_truth.py``) talk to the same host (arxiv.org / export.arxiv.org),
which asks clients to leave at least 3 seconds between automated
requests. Keeping a single module-level timestamp here enforces the gap
across both paths so a benchmark that alternates "fetch PDF → fetch
metadata → fetch PDF" never bursts two calls within milliseconds.
"""

from __future__ import annotations

import threading
import time


_last_request_timestamp: float = 0.0
_lock = threading.Lock()


def wait_for_next_request_slot(min_interval_sec: float = 4.0) -> None:
    """Block until at least *min_interval_sec* has elapsed since the
    previous call across the whole process, then mark the new call."""
    global _last_request_timestamp
    with _lock:
        elapsed = time.time() - _last_request_timestamp
        if elapsed < min_interval_sec:
            time.sleep(min_interval_sec - elapsed)
        _last_request_timestamp = time.time()
