"""Shared subprocess environment for CLI providers."""

from __future__ import annotations

import os


def subprocess_env() -> dict[str, str]:
    """Build an environment dict for CLI subprocess calls.

    Respects REVISICA_RUNTIME_HOME to override $HOME,
    allowing tests and CI to isolate provider config directories.
    """
    env = os.environ.copy()
    runtime_home = env.get("REVISICA_RUNTIME_HOME")
    if runtime_home:
        env["HOME"] = runtime_home
    return env
