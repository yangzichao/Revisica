"""ASyMOB adapter — import symbolic math verification cases.

ASyMOB provides 17K algebraic/calculus challenges with SymPy-verified answers.
Each case is rendered as a LaTeX document with a claim (problem + stated answer)
that our deterministic pipeline should verify or refute.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import json
from pathlib import Path
import re


ASYMOB_LOCAL_PATH = "benchmarks/asymob/raw"


@dataclass
class ASyMOBImportResult:
    imported: int
    manifest_path: Path
    output_dir: Path


def import_asymob_cases(
    limit: int = 10,
    output_dir: str | None = None,
    variation: str = "Original",
) -> ASyMOBImportResult:
    """Import ASyMOB cases for symbolic verification testing.

    Args:
        limit: Maximum number of cases to import.
        output_dir: Override output directory.
        variation: Filter by variation type (default "Original" for base problems).
    """
    local_path = Path.cwd() / ASYMOB_LOCAL_PATH
    if not local_path.exists():
        raise FileNotFoundError(
            f"ASyMOB data not found at {local_path}. "
            "Download with: datasets.load_dataset('Shalyt/ASyMOB-...').save_to_disk(...)"
        )

    from datasets import load_from_disk
    ds = load_from_disk(str(local_path))
    all_examples = list(ds["train"])

    if variation:
        all_examples = [ex for ex in all_examples if ex.get("Variation") == variation]

    examples = all_examples[:limit]

    target_dir = (
        Path(output_dir).expanduser().resolve()
        if output_dir
        else Path.cwd() / "benchmarks" / "asymob" / "cases"
    )
    target_dir.mkdir(parents=True, exist_ok=True)

    cases: list[dict[str, object]] = []
    for index, ex in enumerate(examples, start=1):
        case_id = f"asymob-{ex.get('Index', index)}"
        tex_name = f"{index:03d}_{_slugify(case_id)}.tex"
        tex_path = target_dir / tex_name
        tex_path.write_text(_render_asymob_tex(ex), encoding="utf-8")

        cases.append(
            {
                "id": case_id,
                "file": tex_name,
                "challenge": ex["Challenge"],
                "answer_latex": ex["Answer in Latex"],
                "answer_sympy": ex["Answer in Sympy"],
                "variation": ex.get("Variation", ""),
                "source": ex.get("Source", ""),
                "expected": {
                    "machine_verified_titles": ["Integral equality verified"],
                },
            }
        )

    manifest = {
        "source": "ASyMOB",
        "dataset": "Shalyt/ASyMOB-Algebraic_Symbolic_Mathematical_Operations_Benchmark",
        "variation": variation,
        "imported_at": datetime.now().isoformat(timespec="seconds"),
        "cases": cases,
    }
    manifest_path = target_dir / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=True) + "\n", encoding="utf-8"
    )
    return ASyMOBImportResult(
        imported=len(cases),
        manifest_path=manifest_path,
        output_dir=target_dir,
    )


def _slugify(text: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9]+", "_", text).strip("_")
    return slug[:120] or "asymob_case"


def _render_asymob_tex(record: dict[str, object]) -> str:
    """Render an ASyMOB challenge as a LaTeX document with a verifiable claim.

    The challenge is presented as a theorem statement and the known answer
    is embedded as a "proof" / claim for our pipeline to verify.
    """
    challenge = str(record.get("Challenge", "")).strip()
    answer_latex = str(record.get("Answer in Latex", "")).strip()

    return "\n".join(
        [
            r"\documentclass{article}",
            r"\usepackage{amsmath}",
            r"\usepackage{amsthm}",
            "",
            r"\newtheorem{theorem}{Claim}",
            "",
            r"\begin{document}",
            "",
            r"\begin{theorem}",
            challenge,
            r"\end{theorem}",
            "",
            r"\begin{proof}",
            f"The answer is:",
            r"\[",
            answer_latex,
            r"\]",
            r"\end{proof}",
            "",
            r"\end{document}",
            "",
        ]
    )
