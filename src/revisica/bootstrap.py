from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import shutil

from .templates import (
    PLUGIN_NAME,
    claude_agent_definition_json,
    claude_plugin_manifest,
    codex_agent_prompt,
    codex_plugin_manifest,
    skill_markdown,
)


@dataclass
class PlatformStatus:
    name: str
    cli_path: str | None
    plugin_dir: Path
    agent_path: Path

    @property
    def available(self) -> bool:
        return self.cli_path is not None

    @property
    def installed(self) -> bool:
        return self.plugin_manifest.exists() and self.agent_path.exists()

    @property
    def plugin_manifest(self) -> Path:
        if self.name == "codex":
            return self.plugin_dir / ".codex-plugin" / "plugin.json"
        return self.plugin_dir / ".claude-plugin" / "plugin.json"


def detect_platforms() -> dict[str, PlatformStatus]:
    codex_home = Path(os.environ.get("REVISICA_CODEX_HOME", str(Path.home() / ".codex")))
    claude_home = Path(os.environ.get("REVISICA_CLAUDE_HOME", str(Path.home() / ".claude")))
    return {
        "codex": PlatformStatus(
            name="codex",
            cli_path=shutil.which("codex"),
            plugin_dir=codex_home / "plugins" / PLUGIN_NAME,
            agent_path=codex_home / PLUGIN_NAME / "agents" / "latex-reviewer.txt",
        ),
        "claude": PlatformStatus(
            name="claude",
            cli_path=shutil.which("claude"),
            plugin_dir=claude_home / "plugins" / PLUGIN_NAME,
            agent_path=claude_home / PLUGIN_NAME / "agents" / "latex-reviewer.json",
        ),
    }


def bootstrap(targets: list[str] | None = None, force: bool = False) -> list[str]:
    platforms = detect_platforms()
    selected = targets or list(platforms.keys())
    messages: list[str] = []

    for name in selected:
        platform = platforms[name]
        if not platform.available:
            messages.append(f"[skip] {name}: CLI not found")
            continue

        if name == "codex":
            _install_codex(platform, force=force)
        else:
            _install_claude(platform, force=force)

        messages.append(f"[ok] {name}: assets installed under {platform.plugin_dir}")

    return messages


def _install_codex(platform: PlatformStatus, force: bool) -> None:
    _write_text(
        platform.plugin_dir / ".codex-plugin" / "plugin.json",
        codex_plugin_manifest(),
        force=force,
    )
    _write_text(
        platform.plugin_dir / "skills" / "latex-paper-review" / "SKILL.md",
        skill_markdown(),
        force=force,
    )
    _write_text(platform.agent_path, codex_agent_prompt(), force=force)


def _install_claude(platform: PlatformStatus, force: bool) -> None:
    _write_text(
        platform.plugin_dir / ".claude-plugin" / "plugin.json",
        claude_plugin_manifest(),
        force=force,
    )
    _write_text(
        platform.plugin_dir / "skills" / "latex-paper-review" / "SKILL.md",
        skill_markdown(),
        force=force,
    )
    _write_text(platform.agent_path, claude_agent_definition_json(), force=force)


def _write_text(path: Path, content: str, force: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not force:
        return
    path.write_text(content, encoding="utf-8")
