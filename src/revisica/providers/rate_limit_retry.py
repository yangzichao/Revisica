"""Retry CLI runs that hit a rate limit, and nothing else.

The subscription CLIs fail while a usage window is exhausted; waiting it
out lets long benchmark batches finish. Every other failure — a bad model
name, an auth error, a timeout — fails the same way on every attempt, so
it is returned at once instead of being retried for hours.

The error text must be the CLI's error output only. ``codex exec`` echoes
the whole prompt into stderr, and prompts contain words like "accurate"
and "strategy", so matching all of stderr retried ordinary failures.
"""

from __future__ import annotations

import logging
import re
import subprocess
import time
from typing import Callable

RATE_LIMIT_RETRY_ATTEMPTS = 20
RATE_LIMIT_RETRY_WAIT_SECONDS = 600

# Messages both CLIs print for HTTP 429/529, exhausted usage windows and
# overloaded servers ("rate_limit_error", "You've hit your usage limit",
# "exceeded retry limit, last status: 429 Too Many Requests", ...).
_RATE_LIMIT_PATTERN = re.compile(
    r"rate[ _-]?limit"
    r"|too many requests"
    r"|usage[ _-]limit"
    r"|hit your (?:usage )?limit"
    r"|quota exceeded"
    r"|overloaded"
    r"|\b(?:429|529)\b",
    re.IGNORECASE,
)

# `codex exec` reports failures on stderr lines starting "ERROR:" (or
# "stream error:"); everything else there is the banner and prompt echo.
_CODEX_ERROR_LINE_PATTERN = re.compile(r"^(?:ERROR|stream error)\b.*$", re.IGNORECASE | re.MULTILINE)

_logger = logging.getLogger(__name__)


def mentions_rate_limit(error_text: str) -> bool:
    return bool(_RATE_LIMIT_PATTERN.search(error_text))


def codex_error_lines(stderr: str) -> str:
    return "\n".join(match.group(0) for match in _CODEX_ERROR_LINE_PATTERN.finditer(stderr))


def run_with_rate_limit_retry(
    run_once: Callable[[], subprocess.CompletedProcess],
    is_rate_limited: Callable[[subprocess.CompletedProcess], bool],
    provider_label: str,
) -> subprocess.CompletedProcess:
    """Call ``run_once`` until it is not rate-limited or attempts run out.

    ``subprocess.TimeoutExpired`` propagates from the first attempt that
    times out; the caller turns it into a timed-out result.
    """
    for attempt in range(1, RATE_LIMIT_RETRY_ATTEMPTS + 1):
        completed = run_once()
        if completed.returncode == 0 or not is_rate_limited(completed):
            return completed
        _logger.warning(
            "%s rate-limited (attempt %d/%d), waiting %ds before retry...",
            provider_label, attempt, RATE_LIMIT_RETRY_ATTEMPTS + 1, RATE_LIMIT_RETRY_WAIT_SECONDS,
        )
        time.sleep(RATE_LIMIT_RETRY_WAIT_SECONDS)
    return run_once()


def timeout_stream_text(stream: str | bytes | None) -> str:
    """Text of a stream captured by ``TimeoutExpired``.

    On POSIX, ``TimeoutExpired.stdout`` / ``.stderr`` are bytes even when
    ``subprocess.run`` was called with ``text=True``.
    """
    if stream is None:
        return ""
    if isinstance(stream, bytes):
        return stream.decode("utf-8", errors="replace")
    return stream
