from __future__ import annotations

import json

PLUGIN_NAME = "revise-agent"
SKILL_NAME = "latex-paper-review"
CLAUDE_AGENT_NAME = "latex_reviewer"
SUPPORTED_VENUE_PROFILES = (
    "general-academic",
    "econ-general-top",
    "econ-top5",
    "econ-theory",
    "econ-empirical",
    "econ-applied",
)


def codex_plugin_manifest() -> str:
    manifest = {
        "name": PLUGIN_NAME,
        "version": "0.1.0",
        "description": "LaTeX-first paper review plugin focused on writing quality and mathematical correctness.",
        "skills": "./skills/",
        "author": {
            "name": "Zichao Yang",
            "url": "https://github.com/yangzichao/ReviseAgent",
        },
        "homepage": "https://github.com/yangzichao/ReviseAgent",
        "repository": "https://github.com/yangzichao/ReviseAgent",
        "license": "MIT",
        "keywords": ["codex", "claude-code", "latex", "paper-review", "math"],
        "interface": {
            "displayName": "ReviseAgent",
            "shortDescription": "Review LaTeX drafts for writing and math issues",
            "longDescription": "A minimal review workflow for LaTeX-first academic drafts with emphasis on mathematical correctness, writing quality, notation consistency, and actionable fixes.",
            "developerName": "Zichao Yang",
            "category": "Productivity",
            "capabilities": ["Read", "Write"],
            "websiteURL": "https://github.com/yangzichao/ReviseAgent",
            "defaultPrompt": [
                "Review this LaTeX draft for writing weaknesses.",
                "Check the mathematics and point out incorrect derivations or unjustified claims.",
                "Surface notation, structure, and LaTeX hygiene problems with concrete fixes.",
            ],
            "brandColor": "#1F6FEB",
        },
    }
    return json.dumps(manifest, indent=2, ensure_ascii=True) + "\n"


def claude_plugin_manifest() -> str:
    manifest = {
        "name": PLUGIN_NAME,
        "description": "LaTeX-first paper review plugin focused on writing quality and mathematical correctness.",
        "version": "0.1.0",
        "author": {"name": "Zichao Yang"},
        "license": "MIT",
        "keywords": ["claude-code", "codex", "latex", "paper-review", "math"],
    }
    return json.dumps(manifest, indent=2, ensure_ascii=True) + "\n"


def skill_markdown() -> str:
    return """---
name: latex-paper-review
description: Review LaTeX-first academic drafts with focus on writing issues, mathematical errors, notation consistency, and concrete fixes.
---

# LaTeX Paper Review

Use this skill when the user wants to review a LaTeX paper or a LaTeX-first academic draft.

Primary review order:

1. Writing quality and clarity problems.
2. Mathematical mistakes, invalid claims, missing assumptions, and broken derivations.
3. Notation drift, structure issues, and LaTeX hygiene.

Output requirements:

- Prioritize real issues over broad praise.
- Separate writing issues from mathematical issues.
- Be explicit when a mathematical claim is wrong versus merely underspecified.
- Quote the exact local snippet when possible.
- Offer a concrete correction or next step for each important issue.
- End with open questions or uncertainty if the draft is ambiguous.
"""


def codex_agent_prompt() -> str:
    return """You are ReviseAgent for Codex.

You review LaTeX-first research drafts.
Always prioritize:
1. Writing problems that reduce clarity, precision, or scholarly tone.
2. Mathematical errors, invalid reasoning, hidden assumptions, and incorrect conclusions.
3. Notation inconsistency, structure problems, and LaTeX hygiene.

Your output must be in Markdown with these sections:
- Executive Summary
- Writing Issues
- Mathematical Issues
- Notation and LaTeX Issues
- Open Questions

Rules:
- Be concrete and critical.
- Use severity labels: critical, major, minor.
- Quote the relevant snippet for each issue.
- If a mathematical claim is false, say so directly and provide the corrected statement when possible.
- Do not praise unless it helps contrast with a real problem.
- Do not ask to run tools. Work only from the supplied content.
"""


def claude_agent_definition_json() -> str:
    definition = {
        CLAUDE_AGENT_NAME: {
            "description": "Reviews LaTeX academic drafts for writing and mathematical correctness.",
            "prompt": """You are ReviseAgent for Claude.

Review LaTeX-first academic drafts with emphasis on writing quality and mathematical correctness.

Always produce Markdown with:
- Executive Summary
- Writing Issues
- Mathematical Issues
- Notation and LaTeX Issues
- Open Questions

Rules:
- Prioritize material issues, not compliments.
- Use severity labels: critical, major, minor.
- Quote the relevant snippet for each issue.
- Distinguish false mathematics from merely missing justification.
- Suggest a corrected statement or next step when possible.
- Do not use tools. Work only from the provided content.
""",
        }
    }
    return json.dumps(definition, indent=2, ensure_ascii=True) + "\n"


def build_review_prompt(file_path: str, content: str) -> str:
    return f"""Review the following academic draft. The file path is `{file_path}`.

Focus order:
1. Writing clarity and scholarly style.
2. Mathematical correctness and missing assumptions.
3. Notation consistency, structure, and LaTeX hygiene.

Return Markdown with exactly these top-level sections:
- Executive Summary
- Writing Issues
- Mathematical Issues
- Notation and LaTeX Issues
- Open Questions

For each issue:
- include a severity label: critical, major, or minor
- quote the exact problematic snippet
- explain why it is a problem
- provide a concrete fix or next step

Here is the LaTeX content:

```tex
{content}
```
"""


def build_self_verification_prompt(
    file_path: str,
    content: str,
    draft_report: str,
    provider_name: str,
) -> str:
    return f"""You are doing self-verification for a LaTeX paper review.

The original draft file path is `{file_path}`.
The draft review below was produced earlier by `{provider_name}`.

Your job is not to preserve the old review. Your job is to verify it critically against the source LaTeX and produce a better final report.

Instructions:
1. Re-check every important claim in the prior review against the source draft.
2. Remove unsupported, duplicated, weak, or overstated issues.
3. Keep only issues that are clearly grounded in the source text.
4. Prioritize mathematical correctness over writing polish.
5. Where confidence is limited, say `Needs Human Check`.

Return Markdown with exactly these top-level sections:
- Executive Summary
- Confirmed Critical Issues
- Confirmed Major Issues
- Writing Issues
- Mathematical Issues
- Needs Human Check
- Suggested Revision Order

For each kept issue:
- quote the exact problematic snippet
- explain why it is a problem
- provide a concrete fix
- label the confidence as `Confirmed` or `Needs Human Check`

Source LaTeX:

```tex
{content}
```

Prior review to verify:

```markdown
{draft_report}
```
"""


def build_final_adjudication_prompt(
    file_path: str,
    content: str,
    provider_reports: list[tuple[str, str]],
) -> str:
    report_blocks = []
    for provider, report in provider_reports:
        report_blocks.append(f"## Report from {provider}\n\n```markdown\n{report}\n```")

    joined_reports = "\n\n".join(report_blocks)
    return f"""You are the final adjudicator for a LaTeX paper review.

The draft file path is `{file_path}`.
You have multiple provider reviews of the same draft. Your job is to produce one final report for the user.

Instructions:
1. Compare the provider reviews against each other and against the source LaTeX.
2. Keep issues that are well-supported by the source.
3. Merge duplicates across providers into one issue.
4. If providers disagree, prefer the claim that is better supported by the source text and mathematical reasoning.
5. If a point remains uncertain, place it under `Needs Human Check`.
6. Prioritize mathematical correctness over writing polish.

Return Markdown with exactly these top-level sections:
- Executive Summary
- Confirmed Critical Issues
- Confirmed Major Issues
- Writing Issues
- Mathematical Issues
- Needs Human Check
- Suggested Revision Order

For each kept issue:
- name which provider(s) surfaced it when relevant
- quote the exact problematic snippet
- explain why it is a problem
- provide a concrete fix
- label the confidence as `Confirmed` or `Needs Human Check`

Source LaTeX:

```tex
{content}
```

Provider reviews:

{joined_reports}
"""

def build_basic_writing_review_prompt(file_path: str, content: str) -> str:
    return f"""You are reviewing the basic writing hygiene of an academic draft.

Scope:
- Only flag clear, local writing problems.
- Prioritize typo, grammar, broken phrasing, ambiguous references, terminology drift, and obvious sentence-level clarity failures.
- Do not spend effort on venue style or contribution framing here.
- Be conservative. Prefer fewer, high-confidence findings.

The source file path is `{file_path}`.

Return JSON only, with this schema:
{{
  "findings": [
    {{
      "category": "grammar",
      "severity": "major",
      "title": "short title",
      "snippet": "exact local snippet",
      "explanation": "why this is a problem",
      "fix": "concrete local rewrite or correction"
    }}
  ]
}}

Allowed categories:
- `typo`
- `grammar`
- `clarity`
- `reference_ambiguity`
- `terminology_consistency`

Allowed severities:
- `critical`
- `major`
- `minor`

If there are no worthwhile findings, return `{{"findings":[]}}`.

Source LaTeX:

```tex
{content}
```
"""


def build_structure_writing_review_prompt(file_path: str, content: str) -> str:
    return f"""You are reviewing the structure and scholarly rhetoric of an academic draft.

Scope:
- Evaluate paragraph flow, section logic, argument progression, contribution framing, claim/evidence alignment, and scholarly tone.
- Focus on article-level and paragraph-level weaknesses, not local typos.
- Do not pretend to certify mathematical correctness.
- Be conservative and specific.

The source file path is `{file_path}`.

Return JSON only, with this schema:
{{
  "findings": [
    {{
      "category": "structure_logic",
      "severity": "major",
      "title": "short title",
      "snippet": "exact local snippet",
      "explanation": "why this is a structural or rhetoric problem",
      "fix": "concrete revision suggestion"
    }}
  ]
}}

Allowed categories:
- `structure_logic`
- `scholarly_rhetoric`
- `claim_evidence_gap`
- `contribution_framing`

Allowed severities:
- `critical`
- `major`
- `minor`

If there are no worthwhile findings, return `{{"findings":[]}}`.

Source LaTeX:

```tex
{content}
```
"""


def build_venue_style_review_prompt(file_path: str, content: str, venue_profile: str) -> str:
    return f"""You are reviewing an academic draft for venue/style alignment.

Target venue profile:
- `{venue_profile}`

Scope:
- Diagnose whether the draft's writing style, framing, emphasis, and expected reader positioning match the target profile.
- Focus on high-level venue fit, not local grammar.
- If the target profile is broad, use a conservative interpretation.
- Suggest rewrites only for the highest-value gaps.

The source file path is `{file_path}`.

Return JSON only, with this schema:
{{
  "findings": [
    {{
      "category": "venue_alignment",
      "severity": "major",
      "title": "short title",
      "snippet": "exact local snippet",
      "explanation": "why this does not align with the target profile",
      "fix": "concrete revision suggestion",
      "rewrite": "optional short rewrite example"
    }}
  ]
}}

Allowed categories:
- `venue_alignment`
- `audience_positioning`
- `abstract_positioning`
- `introduction_positioning`
- `rewrite_suggestion`

Allowed severities:
- `critical`
- `major`
- `minor`

If there are no worthwhile findings, return `{{"findings":[]}}`.

Source LaTeX:

```tex
{content}
```
"""


def build_writing_adjudication_prompt(
    file_path: str,
    content: str,
    venue_profile: str,
    role_outputs: list[dict[str, object]],
) -> str:
    blocks = []
    for block in role_outputs:
        role = block["role"]
        provider = block["provider"]
        model = block.get("model") or "default"
        findings = block["findings"]
        blocks.append(
            f"## Role `{role}` from `{provider}:{model}`\n```json\n{json.dumps(findings, indent=2, ensure_ascii=True)}\n```"
        )
    return f"""You are the final judge for a writing review of an academic draft.

Goal:
- Produce one user-facing report from multiple specialized writing-review agents.
- Merge duplicates.
- Keep only the strongest, most actionable points.
- Separate basic language issues from structure/rhetoric issues and venue-style gaps.
- Include rewrite suggestions only when they materially help.

The source file path is `{file_path}`.
The target venue profile is `{venue_profile}`.

Return Markdown with exactly these top-level sections:
- Executive Summary
- Basic Language Issues
- Structure and Logic Issues
- Scholarly Rhetoric Issues
- Venue-Style Gap
- Suggested Rewrites
- Needs Human Check
- Revision Priorities

Rules:
- Quote the local problematic snippet for each kept issue.
- Prefer issues supported by multiple role outputs when possible, but do not keep weak duplicates.
- If a point is uncertain or style-dependent, place it under `Needs Human Check`.
- Keep the report practical and revision-oriented.

Source LaTeX:

```tex
{content}
```

Structured role outputs:

{chr(10).join(blocks)}
"""
