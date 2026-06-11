"""Static assets installed by `revisica bootstrap`.

Plugin manifests, skill markdown, and agent definitions for the Codex and
Claude CLI platforms. Nothing here is a runtime prompt — live review
prompts are the agent definitions in ``agents/definitions/`` plus the
dynamic task builders next to each lane's orchestration code.
"""

from __future__ import annotations

import json

PLUGIN_NAME = "revisica"
SKILL_NAME = "latex-paper-review"
CLAUDE_AGENT_NAME = "latex_reviewer"
def codex_plugin_manifest() -> str:
    manifest = {
        "name": PLUGIN_NAME,
        "version": "0.1.0",
        "description": "LaTeX-first paper review plugin focused on writing quality and mathematical correctness.",
        "skills": "./skills/",
        "author": {
            "name": "Zichao Yang",
            "url": "https://github.com/yangzichao/Revisica",
        },
        "homepage": "https://github.com/yangzichao/Revisica",
        "repository": "https://github.com/yangzichao/Revisica",
        "license": "MIT",
        "keywords": ["codex", "claude-code", "latex", "paper-review", "math"],
        "interface": {
            "displayName": "Revisica",
            "shortDescription": "Review LaTeX drafts for writing and math issues",
            "longDescription": "A minimal review workflow for LaTeX-first academic drafts with emphasis on mathematical correctness, writing quality, notation consistency, and actionable fixes.",
            "developerName": "Zichao Yang",
            "category": "Productivity",
            "capabilities": ["Read", "Write"],
            "websiteURL": "https://github.com/yangzichao/Revisica",
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
    return """You are Revisica for Codex.

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
            "prompt": """You are Revisica for Claude.

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
