"""Capture and persist benchmark provenance metadata.

Every benchmark run records:
- git commit hash and dirty status
- model/provider specs used
- prompt template content hashes (detect prompt drift)
- wall-clock timestamp

Results are appended to a JSONL registry so historical comparisons
can be generated without re-running old benchmarks.
"""

from __future__ import annotations

import ast
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess

from ..core_types import ProviderModelSpec


REGISTRY_PATH = Path("benchmarks/registry.jsonl")


@dataclass
class GitInfo:
    commit: str
    dirty: bool
    branch: str


@dataclass
class PromptHashes:
    """Content hashes for each live prompt source.

    If a hash changes between runs the prompt was modified, which may
    explain score differences. Writing hashes cover the agent definition
    modules in ``agents/definitions/``; the math hash covers the proof
    task builders plus installed agent assets.
    """
    basic_writing: str
    structure_writing: str
    venue_style_writing: str
    writing_judge: str
    writing_self_check: str
    math_proof_review: str


@dataclass
class BenchmarkProvenance:
    timestamp: str
    git: GitInfo
    prompt_hashes: PromptHashes
    suite: str
    providers: list[dict[str, str | None]]
    extra: dict[str, object]


def capture_git_info() -> GitInfo:
    try:
        commit = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True, text=True, check=True, timeout=5,
        ).stdout.strip()
    except Exception:
        commit = "unknown"

    try:
        dirty = bool(subprocess.run(
            ["git", "diff", "--quiet"],
            capture_output=True, check=False, timeout=5,
        ).returncode)
    except Exception:
        dirty = True

    try:
        branch = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True, check=True, timeout=5,
        ).stdout.strip()
    except Exception:
        branch = "unknown"

    return GitInfo(commit=commit, dirty=dirty, branch=branch)


def capture_prompt_hashes() -> PromptHashes:
    """Hash the active prompt/task sources that benchmarks depend on.

    Writing prompts live as agent definition modules under
    ``agents/definitions/``, so we hash each module's file content; any
    edit to the system prompt changes the hash.
    """
    return PromptHashes(
        basic_writing=_hash_definition_module("writing_basic"),
        structure_writing=_hash_definition_module("writing_structure"),
        venue_style_writing=_hash_definition_module("writing_venue"),
        writing_judge=_hash_definition_module("writing_judge"),
        writing_self_check=_hash_definition_module("writing_self_checker"),
        math_proof_review=_hash_math_review_prompt_sources(),
    )


def _hash_definition_module(module_name: str) -> str:
    path = (
        Path(__file__).resolve().parent.parent
        / "agents" / "definitions" / f"{module_name}.py"
    )
    try:
        source = path.read_text(encoding="utf-8")
    except OSError:
        source = ""
    return hashlib.sha256(source.encode()).hexdigest()[:12]


def _hash_math_review_prompt_sources() -> str:
    package_root = Path(__file__).resolve().parent.parent
    repo_root = package_root.parent.parent
    llm_review_path = package_root / "math_llm" / "task.py"
    if not llm_review_path.exists():
        return ""

    source = llm_review_path.read_text(encoding="utf-8")
    module = ast.parse(source, filename=str(llm_review_path))
    target_names = {
        "build_proof_review_task",
        "build_self_check_task",
        "build_adjudication_task",
    }
    segments: list[str] = []
    for node in module.body:
        name = _node_name(node)
        if name not in target_names:
            continue
        segment = ast.get_source_segment(source, node)
        if segment:
            segments.append(segment)

    for filename in (
        "math-proof-reviewer.json",
        "math-self-checker.json",
        "math-adjudicator.json",
    ):
        agent_path = repo_root / "agents" / "claude" / filename
        if agent_path.exists():
            segments.append(agent_path.read_text(encoding="utf-8"))

    for filename in (
        "math-proof-reviewer.md",
        "math-self-checker.md",
        "math-adjudicator.md",
    ):
        agent_path = repo_root / "agents" / "codex" / filename
        if agent_path.exists():
            segments.append(agent_path.read_text(encoding="utf-8"))

    return hashlib.sha256("\n\n".join(segments).encode()).hexdigest()[:12]


def _node_name(node: ast.AST) -> str | None:
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        return node.name
    if isinstance(node, ast.Assign):
        for target in node.targets:
            if isinstance(target, ast.Name):
                return target.id
    if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
        return node.target.id
    return None


def build_provenance(
    suite: str,
    providers: list[ProviderModelSpec] | None = None,
    extra: dict[str, object] | None = None,
) -> BenchmarkProvenance:
    return BenchmarkProvenance(
        timestamp=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        git=capture_git_info(),
        prompt_hashes=capture_prompt_hashes(),
        suite=suite,
        providers=[
            {"provider": spec.provider, "model": spec.model}
            for spec in (providers or [])
        ],
        extra=extra or {},
    )


# ── registry persistence ────────────────────────────────────────────


@dataclass
class RegistryEntry:
    provenance: BenchmarkProvenance
    passed: int
    total: int
    case_results: list[dict[str, object]]
    report_dir: str


def append_to_registry(
    entry: RegistryEntry,
    registry_path: Path | None = None,
) -> Path:
    path = registry_path or REGISTRY_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "provenance": asdict(entry.provenance),
        "passed": entry.passed,
        "total": entry.total,
        "case_results": entry.case_results,
        "report_dir": entry.report_dir,
    }
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=True) + "\n")
    return path


def load_registry(registry_path: Path | None = None) -> list[dict[str, object]]:
    path = registry_path or REGISTRY_PATH
    if not path.exists():
        return []
    entries: list[dict[str, object]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return entries
