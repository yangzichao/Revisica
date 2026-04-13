#!/usr/bin/env python3
"""Analyze ProcessBench benchmark results — compare runs and diagnose failures.

Usage:
    python scripts/analyze_processbench.py benchmarks/runs/processbench-single-agent-*
    python scripts/analyze_processbench.py run_dir_v0 run_dir_v1   # compare two runs
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


def load_run(run_dir: Path) -> dict:
    summary_path = run_dir / "benchmark_summary.json"
    if not summary_path.exists():
        print(f"  [skip] {run_dir.name}: no benchmark_summary.json (still running?)")
        return {}
    return json.loads(summary_path.read_text())


def analyze_single(run_dir: Path) -> None:
    data = load_run(run_dir)
    if not data:
        return

    version = data.get("agent_version") or "default"
    metrics = data.get("suite_metrics", {})
    accuracy = metrics.get("exact_first_error_accuracy", "N/A")
    agg = data["aggregate"]

    print(f"\n{'='*60}")
    print(f"Run: {run_dir.name}")
    print(f"Agent version: {version}")
    print(f"Mode: {data['mode']}")
    print(f"Cases: {agg['cases']}")
    print(f"Passed: {agg['passed']}  Failed: {agg['failed']}  Not scored: {agg['not_scored']}")
    print(f"exact_first_error_accuracy: {accuracy}")
    print(f"{'='*60}")

    for case in data["cases"]:
        status = "PASS" if case["passed"] else "FAIL"
        meta = case.get("metadata", {})
        label = meta.get("label", "?")
        generator = meta.get("generator", "?")
        steps = meta.get("steps", "?")
        msg = case.get("pass_message", "")

        icon = "✓" if case["passed"] else "✗"
        print(f"  {icon} {case['case_id']:20s}  expected_step={label:>3}  steps={steps:>3}  generator={generator}")
        if not case["passed"]:
            print(f"    → {msg}")
            # Try to show what the LLM actually found
            case_dir = run_dir / case["case_id"].replace("-", "_")
            _show_llm_findings(case_dir, case)


def _show_llm_findings(case_dir: Path, case: dict) -> None:
    """Show what the LLM actually found for a failed case."""
    llm_files = sorted(case_dir.glob("llm_proof_review_*.md")) if case_dir.exists() else []
    for llm_file in llm_files:
        content = llm_file.read_text(encoding="utf-8").strip()
        if not content:
            print(f"    [empty output: {llm_file.name}]")
            continue
        # Try to extract step_index from findings
        try:
            # Find JSON in the output
            import re
            json_match = re.search(r'\{.*"findings".*\}', content, re.DOTALL)
            if json_match:
                payload = json.loads(json_match.group())
                findings = payload.get("findings", [])
                if findings:
                    for f in findings[:3]:
                        step = f.get("step_index", "?")
                        title = f.get("title", f.get("detail", ""))[:80]
                        print(f"    found: step={step}, {title}")
                else:
                    print(f"    found: no findings (empty)")
        except Exception:
            # Just show first line of output
            first_line = content.split("\n")[0][:100]
            print(f"    raw: {first_line}...")

    stderr_files = sorted(case_dir.glob("*.stderr.txt")) if case_dir.exists() else []
    for sf in stderr_files:
        content = sf.read_text().strip()
        if "Timed out" in content:
            print(f"    [TIMEOUT]")


def compare_runs(dirs: list[Path]) -> None:
    """Compare multiple runs side by side."""
    runs = []
    for d in dirs:
        data = load_run(d)
        if data:
            runs.append((d, data))

    if len(runs) < 2:
        print("Need at least 2 completed runs to compare.")
        return

    print(f"\n{'='*70}")
    print("COMPARISON")
    print(f"{'='*70}")

    # Header
    headers = ["Case"]
    for d, data in runs:
        version = data.get("agent_version") or "default"
        headers.append(f"{version}")
    print(f"{'  '.join(h.ljust(20) for h in headers)}")
    print("-" * 70)

    # Get all case IDs
    all_cases = {}
    for d, data in runs:
        for case in data["cases"]:
            all_cases[case["case_id"]] = case.get("metadata", {}).get("label", "?")

    for case_id, expected in sorted(all_cases.items()):
        row = [f"{case_id} (exp={expected})"]
        for d, data in runs:
            case = next((c for c in data["cases"] if c["case_id"] == case_id), None)
            if case is None:
                row.append("N/A")
            elif case["passed"]:
                row.append("PASS")
            else:
                msg = case.get("pass_message", "FAIL")
                # Extract predicted step
                import re
                m = re.search(r"predicted first issue step (\S+)", msg)
                predicted = m.group(1) if m else "?"
                row.append(f"FAIL (pred={predicted})")
        print(f"{'  '.join(r.ljust(20) for r in row)}")

    print("-" * 70)
    for d, data in runs:
        version = data.get("agent_version") or "default"
        accuracy = data.get("suite_metrics", {}).get("exact_first_error_accuracy", "?")
        print(f"{version:20s}  accuracy={accuracy}")


def main() -> None:
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    dirs = [Path(arg) for arg in sys.argv[1:]]
    dirs = [d for d in dirs if d.is_dir()]

    if not dirs:
        print("No valid directories found.")
        sys.exit(1)

    for d in dirs:
        analyze_single(d)

    if len(dirs) >= 2:
        compare_runs(dirs)


if __name__ == "__main__":
    main()
