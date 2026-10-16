"""A Codex home for Revisica runs: the user's login, not their instructions.

``codex exec`` puts ``$CODEX_HOME/AGENTS.md`` in front of every prompt,
and no flag turns that off (``-c project_doc_max_bytes=0`` and
``-c instructions=""`` were probed; neither does). Reviews and benchmark
results then depended on whose machine ran them (docs/bugs.md #7).

Revisica points ``CODEX_HOME`` at its own directory, which links back to
the user's ``auth.json`` and ``config.toml`` and has no ``AGENTS.md``.
Codex writes ``auth.json`` through the link (checked with
``codex login --with-api-key`` on codex-cli 0.162.0-alpha.17.2), so a
token refresh during a Revisica run updates the user's own login instead
of leaving them with a used refresh token.
"""

from __future__ import annotations

import logging
import os
import re
import threading
from pathlib import Path

from .subprocess_env import subprocess_env

LINKED_USER_FILES = ("auth.json", "config.toml")
API_KEY_ENV_VARS = ("CODEX_API_KEY", "OPENAI_API_KEY")

_AUTH_STORE_PATTERN = re.compile(
    r"""^\s*cli_auth_credentials_store\s*=\s*["']?(?P<store>[A-Za-z_]+)""",
    re.MULTILINE,
)
_TABLE_HEADER_PATTERN = re.compile(r"^\s*\[", re.MULTILINE)

_logger = logging.getLogger(__name__)


def codex_subprocess_env() -> dict[str, str]:
    """Environment for a Codex CLI subprocess, with the isolated home if usable."""
    env = subprocess_env()
    codex_home = isolated_codex_home()
    if codex_home is not None:
        env["CODEX_HOME"] = str(codex_home)
    return env


def user_codex_home() -> Path:
    """The Codex home the user's own ``codex`` runs with."""
    for variable in ("REVISICA_CODEX_HOME", "CODEX_HOME"):
        value = os.environ.get(variable, "").strip()
        if value:
            return Path(value).expanduser().absolute()
    return _runtime_home() / ".codex"


def revisica_codex_home() -> Path:
    return _runtime_home() / ".revisica" / "codex-home"


def isolated_codex_home() -> Path | None:
    """Prepare and return Revisica's Codex home, or None to use the user's.

    Falls back to the user's home whenever the login might not carry
    over: credentials kept in the keyring instead of ``auth.json``, or
    neither an ``auth.json`` nor an API key env var to log in with.
    """
    user_home = user_codex_home()
    if not _stores_credentials_in_auth_file(user_home):
        return None
    has_auth_file = (user_home / "auth.json").is_file()
    if not has_auth_file and not any(os.environ.get(name) for name in API_KEY_ENV_VARS):
        return None

    codex_home = revisica_codex_home()
    if codex_home == user_home:
        return None
    try:
        codex_home.mkdir(parents=True, exist_ok=True)
        for file_name in LINKED_USER_FILES:
            _mirror_user_file(user_home / file_name, codex_home / file_name)
    except OSError:
        _logger.warning("Could not prepare %s; running Codex with %s", codex_home, user_home, exc_info=True)
        return None
    return codex_home


def _runtime_home() -> Path:
    runtime_home = os.environ.get("REVISICA_RUNTIME_HOME", "").strip()
    return Path(runtime_home).expanduser().absolute() if runtime_home else Path.home()


def _stores_credentials_in_auth_file(user_home: Path) -> bool:
    try:
        config_text = (user_home / "config.toml").read_text(encoding="utf-8")
    except OSError:
        return True
    top_level_text = _TABLE_HEADER_PATTERN.split(config_text, maxsplit=1)[0]
    match = _AUTH_STORE_PATTERN.search(top_level_text)
    return match is None or match.group("store") == "file"


def _mirror_user_file(source: Path, link: Path) -> None:
    """Make ``link`` a symlink to ``source``, or absent when ``source`` is."""
    if not source.exists():
        if link.is_symlink() or link.exists():
            link.unlink()
        return
    if link.is_symlink() and os.readlink(link) == str(source):
        return
    # Several Codex runs start at once; build the link under a private
    # name and rename it into place so none of them sees a half state.
    temporary_link = link.with_name(f".{link.name}.{os.getpid()}.{threading.get_ident()}.tmp")
    temporary_link.unlink(missing_ok=True)
    temporary_link.symlink_to(source)
    os.replace(temporary_link, link)
