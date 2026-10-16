"""Codex runs see the user's login, not their AGENTS.md (docs/bugs.md #7).

``codex exec`` read ``~/.codex/AGENTS.md`` into every Revisica prompt.
Probed on codex-cli 0.162.0-alpha.17.2 with the prompt "reply with the
headings of any AGENTS.md instructions": with the user's home it listed
``# Coding style preferences`` and the rest; with the isolated home it
replied ``NONE`` and still logged in.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

import revisica.providers.cli_codex as cli_codex
from revisica.core_types import AgentSpec
from revisica.providers.codex_home import codex_subprocess_env, isolated_codex_home


@pytest.fixture
def user_codex_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    home = tmp_path / "home"
    codex_home = home / ".codex"
    codex_home.mkdir(parents=True)
    (codex_home / "AGENTS.md").write_text("# Reply in Chinese\n", encoding="utf-8")
    (codex_home / "auth.json").write_text('{"auth_mode": "chatgpt"}\n', encoding="utf-8")
    (codex_home / "config.toml").write_text('model = "gpt-6.1-sol"\n', encoding="utf-8")
    monkeypatch.setenv("HOME", str(home))
    for variable in ("REVISICA_RUNTIME_HOME", "REVISICA_CODEX_HOME", "CODEX_HOME", "CODEX_API_KEY", "OPENAI_API_KEY"):
        monkeypatch.delenv(variable, raising=False)
    return codex_home


def test_isolated_home_links_the_login_and_leaves_out_agents_md(user_codex_home: Path) -> None:
    codex_home = isolated_codex_home()

    assert codex_home == user_codex_home.parent / ".revisica" / "codex-home"
    assert (codex_home / "auth.json").resolve() == (user_codex_home / "auth.json").resolve()
    assert (codex_home / "config.toml").resolve() == (user_codex_home / "config.toml").resolve()
    assert not (codex_home / "AGENTS.md").exists()
    assert codex_subprocess_env()["CODEX_HOME"] == str(codex_home)


def test_writes_to_the_linked_auth_file_reach_the_user_login(user_codex_home: Path) -> None:
    codex_home = isolated_codex_home()

    (codex_home / "auth.json").write_text('{"auth_mode": "refreshed"}\n', encoding="utf-8")

    assert (user_codex_home / "auth.json").read_text(encoding="utf-8") == '{"auth_mode": "refreshed"}\n'


def test_keyring_credentials_keep_the_user_home(user_codex_home: Path) -> None:
    (user_codex_home / "config.toml").write_text('cli_auth_credentials_store = "keyring"\n', encoding="utf-8")

    assert isolated_codex_home() is None
    assert "CODEX_HOME" not in codex_subprocess_env()


def test_auth_store_inside_a_table_is_not_the_top_level_setting(user_codex_home: Path) -> None:
    (user_codex_home / "config.toml").write_text(
        '[profiles.work]\ncli_auth_credentials_store = "keyring"\n', encoding="utf-8"
    )

    assert isolated_codex_home() is not None


def test_no_login_to_carry_over_keeps_the_user_home(user_codex_home: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    (user_codex_home / "auth.json").unlink()

    assert isolated_codex_home() is None

    monkeypatch.setenv("OPENAI_API_KEY", "sk-from-env")
    codex_home = isolated_codex_home()
    assert codex_home is not None
    assert not (codex_home / "auth.json").exists()


def test_logging_out_removes_the_stale_link(user_codex_home: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    codex_home = isolated_codex_home()
    (user_codex_home / "auth.json").unlink()
    monkeypatch.setenv("OPENAI_API_KEY", "sk-from-env")

    isolated_codex_home()

    assert not (codex_home / "auth.json").is_symlink()


def test_run_agent_uses_the_isolated_home_and_turns_off_memories(
    user_codex_home: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[tuple[list[str], dict[str, str]]] = []

    def fake_run(command, **kwargs):
        calls.append((command, kwargs["env"]))
        return subprocess.CompletedProcess(command, 0, stdout="ok", stderr="")

    monkeypatch.setattr(cli_codex.shutil, "which", lambda name: "/fake/bin/codex")
    monkeypatch.setattr(cli_codex.subprocess, "run", fake_run)
    agent_spec = AgentSpec(name="writing-reviewer", system_prompt="Review the paper.")

    cli_codex.CodexCliProvider().run_agent("Task.", agent_spec)
    cli_codex.CodexCliProvider().run_prompt("Prompt.")

    for command, env in calls:
        assert env["CODEX_HOME"] == str(user_codex_home.parent / ".revisica" / "codex-home")
        assert "features.memories=false" in command
