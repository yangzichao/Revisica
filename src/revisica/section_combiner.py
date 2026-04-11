"""Extract LaTeX sections and generate focused section combinations for parallel review.

Instead of sending an entire paper to each LLM call, this module splits the
document into semantic sections and generates targeted pairs/triples so each
worker can analyse a small, focused slice with full attention.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from itertools import combinations


# ── data structures ──────────────────────────────────────────────────


@dataclass
class LatexSection:
    """A single LaTeX section or subsection."""
    level: int  # 0=abstract, 1=\section, 2=\subsection, 3=\subsubsection
    title: str
    line_number: int
    content: str  # body text (excluding the heading command itself)
    raw: str  # original LaTeX heading command


@dataclass
class SectionCombination:
    """A group of sections to be reviewed together."""
    sections: list[LatexSection]
    focus: str  # human-readable description of the analysis focus
    focus_type: str  # machine-readable category tag


# ── section extraction ───────────────────────────────────────────────

# Match \section, \subsection, \subsubsection (optionally starred),
# with an optional short-title and a brace-balanced main title.
_HEADING_RE = re.compile(
    r"(?<!%)\\(?P<cmd>section|subsection|subsubsection)\*?"
    r"(?:\[(?P<short>[^\]]*)\])?"
    r"\{(?P<title>[^}]*(?:\{[^}]*\}[^}]*)*)\}",
)

# Match markdown headings: ## Title, ### Title, #### Title
# (but not inside code blocks — good enough heuristic: must start at col 0)
_MD_HEADING_RE = re.compile(
    r"^(?P<hashes>#{1,4})\s+(?P<title>.+)$",
    re.MULTILINE,
)

# Match \begin{abstract} ... \end{abstract}
_ABSTRACT_RE = re.compile(
    r"\\begin\{abstract\}(?P<body>.*?)\\end\{abstract\}",
    re.DOTALL,
)

_LEVEL_MAP = {"section": 1, "subsection": 2, "subsubsection": 3}


def extract_sections(content: str) -> list[LatexSection]:
    """Parse LaTeX or Markdown headings and return a list of sections.

    Supports:
    - LaTeX: \\section{}, \\subsection{}, \\subsubsection{}
    - Markdown: # Title, ## Title, ### Title, #### Title
    - LaTeX abstract environment: \\begin{abstract}...\\end{abstract}
    - Markdown abstract heading: #### Abstract / ## Abstract
    """
    lines = content.split("\n")
    # (line_no, level, title, raw_heading_text)
    matches: list[tuple[int, int, str, str]] = []

    # Extract LaTeX abstract environment first
    abstract_match = _ABSTRACT_RE.search(content)
    if abstract_match:
        abs_line = content[:abstract_match.start()].count("\n") + 1
        matches.append((abs_line, 0, "Abstract", r"\begin{abstract}"))

    # Try LaTeX headings first
    has_latex_headings = False
    for line_idx, line in enumerate(lines, start=1):
        stripped = line.lstrip()
        if stripped.startswith("%"):
            continue
        m = _HEADING_RE.search(line)
        if m:
            level = _LEVEL_MAP[m.group("cmd")]
            title = m.group("title").strip()
            matches.append((line_idx, level, title, m.group(0)))
            has_latex_headings = True

    # If no LaTeX headings found, try Markdown headings
    if not has_latex_headings:
        for line_idx, line in enumerate(lines, start=1):
            m = _MD_HEADING_RE.match(line)
            if m:
                hashes = m.group("hashes")
                title = m.group("title").strip()
                # Map: # → 1, ## → 1, ### → 2, #### → 3
                # (Most markdown papers use ## as top-level section)
                n_hashes = len(hashes)
                if n_hashes <= 2:
                    level = 1
                elif n_hashes == 3:
                    level = 2
                else:
                    level = 3
                # Detect abstract heading
                if title.lower().strip() == "abstract":
                    level = 0
                matches.append((line_idx, level, title, line.strip()))

    if not matches:
        return []

    # Sort by line number (abstract may appear before or after first heading)
    matches.sort(key=lambda x: x[0])

    sections: list[LatexSection] = []
    for i, (line_no, level, title, raw_heading) in enumerate(matches):
        if level == 0 and abstract_match:
            # Abstract: use the extracted body directly
            body = abstract_match.group("body").strip()
            sections.append(
                LatexSection(
                    level=0,
                    title=title,
                    line_number=line_no,
                    content=body,
                    raw=raw_heading,
                )
            )
            continue

        # Content = lines after the heading, up to the next heading
        start_line = line_no  # heading line (1-indexed)
        end_line = matches[i + 1][0] - 1 if i + 1 < len(matches) else len(lines)
        # Body starts on the line AFTER the heading
        body_lines = lines[start_line : end_line]  # start_line is 1-indexed, so [start_line:] skips heading
        sections.append(
            LatexSection(
                level=level,
                title=title,
                line_number=line_no,
                content="\n".join(body_lines),
                raw=raw_heading,
            )
        )
    return sections


# ── combination strategies ───────────────────────────────────────────

# Mapping from keyword (or phrase) → role tag.
# Multi-word phrases are checked first, then single words with word-boundary matching.
_ROLE_RULES: list[tuple[str, str, bool]] = [
    # (pattern, role_tag, is_phrase)
    # Phrases — checked via substring
    ("related work", "related", True),
    ("prior work", "related", True),
    ("main result", "theory", True),
    ("main results", "theory", True),
    ("concluding remarks", "conclusion", True),
    ("concluding comment", "conclusion", True),
    ("incomplete information", "method", True),  # econ-specific
    # Single words — checked via word-boundary regex
    ("abstract", "abstract", False),
    ("introduction", "intro", False),
    ("intro", "intro", False),
    ("conclusion", "conclusion", False),
    ("conclusions", "conclusion", False),
    ("concluding", "conclusion", False),
    ("discussion", "conclusion", False),
    ("summary", "conclusion", False),
    ("methodology", "method", False),
    ("methods", "method", False),
    ("method", "method", False),
    ("approach", "method", False),
    ("framework", "method", False),
    ("model", "method", False),
    ("results", "result", False),
    ("result", "result", False),
    ("findings", "result", False),
    ("experiments", "result", False),
    ("evaluation", "result", False),
    ("applications", "result", False),
    ("simulations", "result", False),
    ("numerical", "result", False),
    ("theorems", "theory", False),
    ("theorem", "theory", False),
    ("theory", "theory", False),
    ("proofs", "theory", False),
    ("proof", "theory", False),
    ("appendix", "theory", False),
    ("lemma", "theory", False),
    ("proposition", "theory", False),
    ("optimal", "theory", False),
    ("stability", "theory", False),
    ("literature", "related", False),
    ("background", "related", False),
    ("definitions", "definition", False),
    ("definition", "definition", False),
    ("setup", "definition", False),
    ("notation", "definition", False),
    ("preliminaries", "definition", False),
    ("setting", "definition", False),
    ("primer", "definition", False),
]

# Pre-compile word-boundary patterns
_ROLE_PATTERNS: list[tuple[re.Pattern[str], str]] = []
for _kw, _tag, _is_phrase in _ROLE_RULES:
    if _is_phrase:
        _ROLE_PATTERNS.append((re.compile(re.escape(_kw), re.IGNORECASE), _tag))
    else:
        _ROLE_PATTERNS.append((re.compile(r"\b" + re.escape(_kw) + r"\b", re.IGNORECASE), _tag))


def _classify_section(section: LatexSection) -> set[str]:
    """Return a set of role tags for a section based on its title.

    Uses word-boundary matching to avoid false positives like
    "Formal Model" matching "model".
    """
    title = section.title
    if section.level == 0 and title.lower() == "abstract":
        return {"abstract"}
    tags: set[str] = set()
    for pattern, tag in _ROLE_PATTERNS:
        if pattern.search(title):
            tags.add(tag)
    return tags


def generate_combinations(
    sections: list[LatexSection],
    *,
    max_combinations: int = 30,
) -> list[SectionCombination]:
    """Generate meaningful section pairs/triples for focused cross-analysis.

    Strategy:
    1. Semantic pairs — sections whose roles naturally need cross-checking
       (e.g. abstract ↔ conclusion, definitions ↔ theorems, claims ↔ results).
    2. Adjacent pairs — consecutive sections that should flow logically.
    3. All-pairs for short papers — if the paper has ≤ 6 top-level sections,
       every pair is generated.
    """
    if not sections:
        return []

    classified: list[tuple[LatexSection, set[str]]] = [
        (sec, _classify_section(sec)) for sec in sections
    ]

    combos: list[SectionCombination] = []
    seen: set[tuple[int, ...]] = set()

    def _add(secs: list[LatexSection], focus: str, focus_type: str) -> None:
        if len(combos) >= max_combinations:
            return
        key = tuple(sorted(s.line_number for s in secs))
        if key in seen:
            return
        seen.add(key)
        combos.append(SectionCombination(sections=secs, focus=focus, focus_type=focus_type))

    # ── 1. Semantic pairs ────────────────────────────────────────────
    by_role: dict[str, list[LatexSection]] = {}
    for sec, tags in classified:
        for tag in tags:
            by_role.setdefault(tag, []).append(sec)

    _SEMANTIC_PAIRS: list[tuple[str, str, str, str]] = [
        ("abstract", "conclusion", "Check whether claims in the abstract are supported by the conclusion", "claim_consistency"),
        ("intro", "conclusion", "Check whether the introduction's promises match the conclusion's deliverables", "claim_consistency"),
        ("intro", "result", "Check whether the introduction's claims are backed by the results section", "claim_consistency"),
        ("definition", "theory", "Cross-check notation and definitions used in theorems against their definitions", "notation_cross_check"),
        ("method", "result", "Verify that methods described actually match the results reported", "method_result_alignment"),
        ("method", "theory", "Check consistency between the model/methodology and theoretical claims", "method_theory_alignment"),
        ("related", "intro", "Check that related work is properly contextualized against the introduction", "positioning_check"),
    ]

    for role_a, role_b, focus, focus_type in _SEMANTIC_PAIRS:
        for sec_a in by_role.get(role_a, []):
            for sec_b in by_role.get(role_b, []):
                if sec_a.line_number != sec_b.line_number:
                    _add([sec_a, sec_b], focus, focus_type)

    # definition ↔ theory triples (definition + theorem section + conclusion)
    for sec_def in by_role.get("definition", []):
        for sec_thm in by_role.get("theory", []):
            for sec_conc in by_role.get("conclusion", []):
                _add(
                    [sec_def, sec_thm, sec_conc],
                    "Cross-check definitions, theorem statements, and conclusions for consistency",
                    "notation_cross_check",
                )

    # ── 2. Adjacent pairs (logical flow) ─────────────────────────────
    top_sections = [sec for sec in sections if sec.level <= 1]
    for i in range(len(top_sections) - 1):
        _add(
            [top_sections[i], top_sections[i + 1]],
            f"Check logical flow and transition between '{top_sections[i].title}' and '{top_sections[i + 1].title}'",
            "logical_flow",
        )

    # ── 3. All pairs for short papers ────────────────────────────────
    if len(top_sections) <= 6:
        for sec_a, sec_b in combinations(top_sections, 2):
            _add(
                [sec_a, sec_b],
                f"Cross-reference '{sec_a.title}' with '{sec_b.title}' for consistency",
                "general_cross_check",
            )

    return combos


# ── prompt building ──────────────────────────────────────────────────


def build_section_combo_task(
    combination: SectionCombination,
    file_path: str,
) -> str:
    """Build a focused review prompt for a section combination.

    The prompt includes only the relevant section content so the LLM
    can give it full attention without long-context distraction.
    """
    section_blocks = []
    for sec in combination.sections:
        section_blocks.append(
            f"### Section: {sec.title} (line {sec.line_number})\n"
            f"```tex\n{sec.content}\n```"
        )
    joined = "\n\n".join(section_blocks)

    return (
        f"You are performing a focused cross-section review of the academic draft at `{file_path}`.\n\n"
        f"**Analysis focus:** {combination.focus}\n\n"
        f"Below are the relevant sections extracted from the paper. "
        f"Analyse ONLY these sections for the stated focus. "
        f"Be specific, cite exact snippets, and be conservative — only flag genuine issues.\n\n"
        f"{joined}\n\n"
        f"Return JSON with a 'findings' array. Each finding needs: "
        f"category, severity, title, snippet, explanation, fix.\n"
        f"Allowed categories: claim_inconsistency, notation_mismatch, logic_gap, "
        f"unsupported_claim, flow_break, cross_reference_error.\n"
        f"Allowed severities: critical, major, minor.\n"
        f'If no findings, return {{"findings": []}}.'
    )


def build_section_combo_agent_def() -> dict[str, object]:
    """Return the Claude agent definition for focused section cross-checking."""
    return {
        "description": "Cross-checks pairs of paper sections for consistency and logical flow.",
        "prompt": (
            "You are a cross-section reviewer for academic LaTeX drafts. "
            "You receive a small set of sections and a specific analysis focus. "
            "Your job is to find inconsistencies, unsupported claims, notation drift, "
            "and logical gaps BETWEEN the given sections. "
            "Be conservative — only flag genuine issues. "
            "Return JSON with a 'findings' array. "
            "Each finding needs: category, severity, title, snippet, explanation, fix. "
            "Allowed categories: claim_inconsistency, notation_mismatch, logic_gap, "
            "unsupported_claim, flow_break, cross_reference_error. "
            "Allowed severities: critical, major, minor. "
            'If no findings, return {"findings": []}.'
        ),
        "tools": ["Read", "Glob", "Grep"],
    }
