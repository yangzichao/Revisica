"""Render benchmark history from the JSONL registry.

Produces a markdown report with:
- Summary table of all runs (suite, commit, pass rate, timestamp)
- Per-suite trend (pass rate over time)
- Prompt-drift detection (highlight when prompt hashes changed)
"""

from __future__ import annotations

import json
from pathlib import Path

from .provenance import REGISTRY_PATH, load_registry


def render_history(
    registry_path: Path | None = None,
    suite_filter: str | None = None,
    limit: int | None = None,
) -> str:
    entries = load_registry(registry_path)
    if suite_filter:
        entries = [e for e in entries if e.get("provenance", {}).get("suite") == suite_filter]
    if limit:
        entries = entries[-limit:]

    if not entries:
        return "No benchmark runs recorded yet.\n"

    lines = [
        "# Revisica Benchmark History",
        "",
    ]

    # ── summary table ────────────────────────────────────────────────
    lines.append("## Runs")
    lines.append("")
    lines.append("| # | Timestamp | Suite | Commit | Dirty | Pass Rate | Prompts Changed |")
    lines.append("|---|-----------|-------|--------|-------|-----------|-----------------|")

    prev_hashes: dict[str, str | None] = {}
    for idx, entry in enumerate(entries, 1):
        prov = entry.get("provenance", {})
        git = prov.get("git", {})
        commit = git.get("commit", "?")[:8]
        dirty = "yes" if git.get("dirty") else "no"
        ts = prov.get("timestamp", "?")
        suite = prov.get("suite", "?")
        passed = entry.get("passed", 0)
        total = entry.get("total", 0)
        rate = f"{passed}/{total}"

        current_hashes = json.dumps(prov.get("prompt_hashes", {}), sort_keys=True)
        suite_key = suite
        prompt_changed = ""
        if suite_key in prev_hashes:
            if prev_hashes[suite_key] != current_hashes:
                prompt_changed = "**changed**"
        prev_hashes[suite_key] = current_hashes

        lines.append(f"| {idx} | {ts} | {suite} | `{commit}` | {dirty} | {rate} | {prompt_changed} |")

    # ── per-suite trends ─────────────────────────────────────────────
    suites: dict[str, list[dict[str, object]]] = {}
    for entry in entries:
        suite = entry.get("provenance", {}).get("suite", "?")
        suites.setdefault(suite, []).append(entry)

    for suite, runs in suites.items():
        lines.extend(["", f"## Trend: {suite}", ""])
        lines.append("```")
        for run in runs:
            prov = run.get("provenance", {})
            ts = prov.get("timestamp", "?")[:16]
            commit = prov.get("git", {}).get("commit", "?")[:8]
            passed = run.get("passed", 0)
            total = run.get("total", 0)
            pct = (passed / total * 100) if total else 0
            bar = "#" * int(pct / 5) + "." * (20 - int(pct / 5))
            lines.append(f"{ts}  {commit}  [{bar}] {passed}/{total} ({pct:.0f}%)")
        lines.append("```")

    # ── per-case detail for latest run of each suite ─────────────────
    for suite, runs in suites.items():
        latest = runs[-1]
        cases = latest.get("case_results", [])
        if not cases:
            continue
        lines.extend(["", f"## Latest: {suite}", ""])
        for case in cases:
            status = "PASS" if case.get("passed") else "FAIL"
            lines.append(f"- `{case.get('case_id', '?')}`: {status} — {case.get('message', '')}")

    return "\n".join(lines) + "\n"


def write_history_report(
    output_path: Path | None = None,
    registry_path: Path | None = None,
    suite_filter: str | None = None,
    limit: int | None = None,
) -> Path:
    content = render_history(
        registry_path=registry_path,
        suite_filter=suite_filter,
        limit=limit,
    )
    target = output_path or Path("benchmarks/history.md")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return target
