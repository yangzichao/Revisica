"""Lightweight .tex → Markdown parser (no external dependencies).

This is a fallback when Pandoc is not installed.  It handles common
LaTeX structures (sections, math, basic formatting) but does NOT
expand macros or handle complex packages.  For best results, use
the Pandoc parser instead.
"""

from __future__ import annotations

import re
from pathlib import Path

from .base import BaseParser


class TexParser(BaseParser):
    """Basic regex-based LaTeX to Markdown conversion."""

    name = "tex-basic"

    def can_handle(self, path: Path) -> bool:
        return path.suffix.lower() == ".tex"

    @classmethod
    def is_available(cls) -> bool:
        return True  # No external dependencies

    def parse(self, path: Path) -> str:
        content = path.read_text(encoding="utf-8")
        return _tex_to_markdown(content)


def _tex_to_markdown(tex: str) -> str:
    """Convert LaTeX content to Markdown with best-effort translation."""
    # Strip preamble (everything before \begin{document})
    document_match = re.search(
        r"\\begin\{document\}(.*?)\\end\{document\}",
        tex,
        re.DOTALL,
    )
    body = document_match.group(1) if document_match else tex

    # Extract title and author from preamble
    title = _extract_command(tex, "title")
    author = _extract_command(tex, "author")

    lines: list[str] = []
    if title:
        lines.append(f"# {title}")
        lines.append("")
    if author:
        lines.append(f"Author: {author}")
        lines.append("")

    # Strip \maketitle
    body = re.sub(r"\\maketitle", "", body)

    # Convert sections
    body = re.sub(r"\\section\{([^}]+)\}", r"## \1", body)
    body = re.sub(r"\\subsection\{([^}]+)\}", r"### \1", body)
    body = re.sub(r"\\subsubsection\{([^}]+)\}", r"#### \1", body)

    # Convert display math: \[ ... \] → $$ ... $$
    body = re.sub(r"\\\[", "$$", body)
    body = re.sub(r"\\\]", "$$", body)

    # Convert equation environments → $$ ... $$
    body = re.sub(
        r"\\begin\{(equation|align|gather|multline)\*?\}",
        "$$",
        body,
    )
    body = re.sub(
        r"\\end\{(equation|align|gather|multline)\*?\}",
        "$$",
        body,
    )

    # Convert theorem-like environments
    for environment_name in ("theorem", "lemma", "proposition", "corollary", "definition", "remark"):
        body = re.sub(
            rf"\\begin\{{{environment_name}\}}",
            f"\n**{environment_name.capitalize()}.**",
            body,
        )
        body = re.sub(rf"\\end\{{{environment_name}\}}", "", body)

    # Convert proof environment
    body = re.sub(r"\\begin\{proof\}", "\n*Proof.*", body)
    body = re.sub(r"\\end\{proof\}", "∎\n", body)

    # Convert itemize/enumerate
    body = re.sub(r"\\begin\{(itemize|enumerate)\}", "", body)
    body = re.sub(r"\\end\{(itemize|enumerate)\}", "", body)
    body = re.sub(r"\\item\s*", "- ", body)

    # Convert text formatting
    body = re.sub(r"\\textbf\{([^}]+)\}", r"**\1**", body)
    body = re.sub(r"\\textit\{([^}]+)\}", r"*\1*", body)
    body = re.sub(r"\\emph\{([^}]+)\}", r"*\1*", body)

    # Strip remaining simple commands
    body = re.sub(r"\\(label|ref|eqref|cite)\{[^}]*\}", "", body)
    body = re.sub(r"\\(noindent|medskip|bigskip|newpage|clearpage)", "", body)

    # Clean up whitespace
    body = re.sub(r"\n{3,}", "\n\n", body)

    lines.append(body.strip())
    return "\n".join(lines)


def _extract_command(tex: str, command_name: str) -> str:
    """Extract the argument of a LaTeX command like \\title{...}."""
    match = re.search(rf"\\{command_name}\{{([^}}]+)\}}", tex)
    return match.group(1).strip() if match else ""
