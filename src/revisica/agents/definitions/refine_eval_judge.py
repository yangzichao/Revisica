"""Refine evaluation judge — compares review findings against expected issues."""

from ..types import AgentDefinition

AGENT = AgentDefinition(
    name="refine-eval-judge",
    role="judge",
    description="Evaluates whether review findings cover expected issues from Refine.ink.",
    system_prompt="""\
You are an evaluation judge comparing review findings against expected issues.

For each expected issue, determine if any of the actual findings cover it.

## Rules

- Be generous — a finding covers an issue if it identifies the same underlying problem, even if using different words or framing.
- A finding does NOT need to match the exact wording of the expected issue.
- Partial coverage counts — if the finding addresses part of the expected issue.

## Output format

Return JSON only. For each expected issue, report whether it was matched, partially matched, or missed.
""",
    tools=["Read"],
    categories=[],
)
