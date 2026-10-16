"""LLM proof review must read the text its line numbers refer to.

In ``revisica review`` the math lane extracts blueprints from the ingested
Markdown, but the proof-review task pointed at the original file: for
``examples/proof_blueprint_demo.tex`` the task said "Theorem line: 2" while
the theorem sits on line 9 of the .tex, and a PDF input sent the agents to
read the PDF.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

import revisica.math_llm.review as math_llm_review
from revisica.bootstrap import PlatformStatus
from revisica.core_types import ReviewResult
from revisica.math_review import review_math_file

_DEMO_PAPER = Path(__file__).resolve().parents[1] / "examples" / "proof_blueprint_demo.tex"

# Pandoc's Markdown for proof_blueprint_demo.tex.
PANDOC_MARKDOWN = """::: theorem
**Theorem 1**. *We have $$\\int_0^1 x^2 \\, dx = \\frac{1}{2}.$$*
:::

::: proof
*Proof.* Clearly, the antiderivative of $x^2$ is $x^2/2$. Therefore $$\\int_0^1 x^2 \\, dx = \\frac{1}{2}.$$ Thus the theorem follows. ◻
:::
"""


def test_proof_review_task_points_at_the_ingested_text(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    platforms = {
        "claude": PlatformStatus("claude", "/fake/bin/claude", tmp_path / "plugin", tmp_path / "agent.json"),
        "codex": PlatformStatus("codex", None, tmp_path / "plugin", tmp_path / "agent.txt"),
    }
    monkeypatch.setattr(math_llm_review, "detect_platforms", lambda: platforms)
    monkeypatch.setattr(math_llm_review, "bootstrap", lambda *args, **kwargs: [])
    review_tasks: list[str] = []

    def fake_run_provider_agent(provider_name, task_prompt, agent_spec, *args, **kwargs):
        review_tasks.append(task_prompt)
        return ReviewResult(provider_name, None, [], 0, '{"findings": []}', "")

    monkeypatch.setattr(math_llm_review, "run_provider_agent", fake_run_provider_agent)

    run = review_math_file(
        str(_DEMO_PAPER),
        output_dir=str(tmp_path / "math"),
        llm_proof_review=True,
        targets=["claude"],
        content_override=PANDOC_MARKDOWN,
    )

    proof_review_task = next(task for task in review_tasks if task.startswith("Review the proof obligations"))
    reviewed_path = Path(re.search(r"draft at `([^`]+)`", proof_review_task).group(1))
    assert reviewed_path == run.run_dir / "proof_blueprint_demo.normalized.md"
    theorem_line = int(re.search(r"Theorem line: (\d+)", proof_review_task).group(1))
    reviewed_lines = reviewed_path.read_text(encoding="utf-8").splitlines()
    assert "Theorem 1" in reviewed_lines[theorem_line - 1]
