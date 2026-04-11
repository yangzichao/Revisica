"""Extract verifiable mathematical claims from paper content, paragraph by paragraph.

Instead of giving the whole paper to a single claim-verifier and hoping it
finds everything, this module pre-extracts individual claims so each one can
be verified in a focused, parallel SymPy task.

Key insight from Refine.ink benchmark: the two missed findings (Footnote 16
comparative static, Proposition 1 limiting direction) both required
step-by-step derivation of a *specific* claim.  A whole-paper verifier times
out before reaching them.  Per-claim tasks are small, focused, and fast.
"""
from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class ExtractedClaim:
    """A single verifiable mathematical claim extracted from the paper."""
    claim_id: str
    paragraph_text: str  # the paragraph or footnote containing the claim
    claim_text: str  # the specific claim statement
    claim_type: str  # category of claim
    context: str  # surrounding definitions/equations needed to verify
    line_number: int
    source_label: str  # e.g. "Footnote 16", "Discussion of Proposition 2", "Section 3.1"


# ── paragraph splitting ──────────────────────────────────────────────

_FOOTNOTE_RE = re.compile(
    r"\[\^(?P<num>\d+)\]:\s*(?P<text>.+?)(?=\n\[\^|\n\n|\Z)",
    re.DOTALL,
)

_DISPLAY_MATH_RE = re.compile(
    r"\$\$(.+?)\$\$",
    re.DOTALL,
)

_INLINE_MATH_RE = re.compile(r"\$([^$]+)\$")

# Patterns that signal a verifiable claim
_CLAIM_SIGNALS = [
    # "it can be verified that ..."
    re.compile(r"it can be (?:verified|shown|checked) that", re.IGNORECASE),
    # "one can show ..."
    re.compile(r"one can (?:show|verify|check) (?:that )?", re.IGNORECASE),
    # "is increasing/decreasing in ..."
    re.compile(r"is (?:increasing|decreasing|monotone|convex|concave) (?:in|with respect to)", re.IGNORECASE),
    # "tends to", "converges to", "approaches"
    re.compile(r"(?:tends|converges|approaches) to", re.IGNORECASE),
    # "equals", "is equal to", "is given by"
    re.compile(r"(?:equals|is equal to|is given by|reduces to|simplifies to)", re.IGNORECASE),
    # "≥", "≤", ">"," <" in math contexts
    re.compile(r"(?:greater|less|larger|smaller) than", re.IGNORECASE),
    # "if and only if"
    re.compile(r"if and only if", re.IGNORECASE),
    # "for all", "for every", "for any"
    re.compile(r"for (?:all|every|any|each) ", re.IGNORECASE),
    # comparative statics phrasing
    re.compile(r"(?:the ratio|the expression|the term|the quantity) .{0,50}(?:increasing|decreasing)", re.IGNORECASE),
    # "straightforward to verify"
    re.compile(r"straightforward to (?:verify|show|check)", re.IGNORECASE),
    # "follows from/that"
    re.compile(r"(?:it follows|this follows|which follows) (?:from|that)", re.IGNORECASE),
    # "by substitution/differentiation"
    re.compile(r"by (?:substitut|differentiat|integrat|expand|simplif)", re.IGNORECASE),
    # proposition/theorem interpretation claims
    re.compile(r"(?:proposition|theorem|lemma|corollary) \d+ (?:shows|implies|states|establishes|says)", re.IGNORECASE),
    # "the limit/derivative/integral is/equals"
    re.compile(r"the (?:limit|derivative|integral|expectation|variance|probability) (?:is|equals|of)", re.IGNORECASE),
]


def _has_math(text: str) -> bool:
    """Check if text contains mathematical notation."""
    return bool(_INLINE_MATH_RE.search(text)) or bool(_DISPLAY_MATH_RE.search(text))


def _has_claim_signal(text: str) -> bool:
    """Check if text contains phrasing that signals a verifiable claim."""
    return any(pat.search(text) for pat in _CLAIM_SIGNALS)


# ── claim extraction ─────────────────────────────────────────────────


def extract_claims(content: str) -> list[ExtractedClaim]:
    """Extract verifiable mathematical claims from paper content.

    Scans:
    1. Each paragraph for claim-signal language + math
    2. Footnotes (often contain "it can be verified" claims)
    3. Discussion paragraphs after theorems/propositions
    """
    claims: list[ExtractedClaim] = []
    lines = content.split("\n")
    claim_counter = 0

    # ── 1. Extract footnote claims ───────────────────────────────────
    for m in _FOOTNOTE_RE.finditer(content):
        fn_num = m.group("num")
        fn_text = m.group("text").strip()
        fn_line = content[:m.start()].count("\n") + 1

        if _has_math(fn_text) and _has_claim_signal(fn_text):
            claim_counter += 1
            claims.append(ExtractedClaim(
                claim_id=f"claim-{claim_counter}",
                paragraph_text=fn_text,
                claim_text=_extract_claim_sentence(fn_text),
                claim_type="footnote_claim",
                context=_gather_context(content, fn_line, radius=30),
                line_number=fn_line,
                source_label=f"Footnote {fn_num}",
            ))

    # ── 2. Extract paragraph-level claims ────────────────────────────
    paragraphs = _split_paragraphs(content)

    for para_text, para_line in paragraphs:
        if not _has_math(para_text):
            continue
        if not _has_claim_signal(para_text):
            continue
        # Skip if already captured as a footnote
        if any(c.line_number == para_line and c.claim_type == "footnote_claim" for c in claims):
            continue

        claim_counter += 1
        source = _identify_source_label(content, para_line)
        claims.append(ExtractedClaim(
            claim_id=f"claim-{claim_counter}",
            paragraph_text=para_text,
            claim_text=_extract_claim_sentence(para_text),
            claim_type=_classify_claim(para_text),
            context=_gather_context(content, para_line, radius=40),
            line_number=para_line,
            source_label=source,
        ))

    return claims


def _split_paragraphs(content: str) -> list[tuple[str, int]]:
    """Split content into (paragraph_text, start_line_number) pairs."""
    lines = content.split("\n")
    paragraphs: list[tuple[str, int]] = []
    current_lines: list[str] = []
    current_start = 1

    for i, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not stripped:
            if current_lines:
                paragraphs.append(("\n".join(current_lines), current_start))
                current_lines = []
            current_start = i + 1
        else:
            if not current_lines:
                current_start = i
            current_lines.append(line)

    if current_lines:
        paragraphs.append(("\n".join(current_lines), current_start))

    return paragraphs


def _extract_claim_sentence(text: str) -> str:
    """Extract the core claim sentence from a paragraph.

    Looks for sentences containing claim signals and returns them.
    Falls back to the first sentence with math.
    """
    # Split into sentences (rough heuristic)
    sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z$\\])', text)

    # First try: sentence with claim signal
    for sent in sentences:
        if _has_claim_signal(sent):
            return sent.strip()

    # Fallback: first sentence with math
    for sent in sentences:
        if _has_math(sent):
            return sent.strip()

    return text[:500].strip()


def _gather_context(content: str, line_number: int, radius: int = 30) -> str:
    """Gather surrounding context (definitions, equations) for verification.

    Looks at lines before and after the claim for relevant definitions.
    """
    lines = content.split("\n")
    start = max(0, line_number - radius - 1)
    end = min(len(lines), line_number + radius)
    context_lines = lines[start:end]

    # Filter to keep only lines with math, definitions, or section headings
    relevant: list[str] = []
    for line in context_lines:
        stripped = line.strip()
        if not stripped:
            continue
        if _has_math(stripped) or stripped.startswith("#") or stripped.startswith("\\"):
            relevant.append(stripped)
        elif any(kw in stripped.lower() for kw in ["define", "denote", "let ", "where ", "assume", "suppose"]):
            relevant.append(stripped)

    return "\n".join(relevant[-40:])  # cap context size


def _identify_source_label(content: str, line_number: int) -> str:
    """Identify which section/theorem/proposition a paragraph belongs to."""
    lines = content.split("\n")

    # Look backwards for the nearest heading or theorem-like environment
    for i in range(line_number - 1, max(0, line_number - 50), -1):
        line = lines[i].strip() if i < len(lines) else ""

        # Markdown heading
        m = re.match(r"^(#{1,4})\s+(.+)$", line)
        if m:
            return m.group(2).strip()[:80]

        # LaTeX heading
        m = re.search(r"\\(?:section|subsection)\{([^}]+)\}", line)
        if m:
            return m.group(1).strip()[:80]

        # Theorem-like
        m = re.search(r"\\begin\{(theorem|proposition|lemma|corollary)\}", line)
        if m:
            return f"{m.group(1).title()} near line {i+1}"

        # "Proposition N" / "Theorem N" in text
        m = re.search(r"(Proposition|Theorem|Lemma|Corollary)\s+\d+", line)
        if m:
            return f"Discussion of {m.group(0)}"

    return f"Paragraph near line {line_number}"


def _classify_claim(text: str) -> str:
    """Classify the type of mathematical claim."""
    lower = text.lower()
    if re.search(r"increas|decreas|monoton", lower):
        return "comparative_static"
    if re.search(r"converge|tends to|limit|approach", lower):
        return "limit_claim"
    if re.search(r"equal|given by|simplif|reduc", lower):
        return "algebraic_identity"
    if re.search(r"if and only if|implies|necessary|sufficient", lower):
        return "logical_equivalence"
    if re.search(r"for all|for every|for any", lower):
        return "universal_claim"
    if re.search(r"deriv|differentiat|integrat", lower):
        return "calculus_claim"
    if re.search(r"proposition|theorem|corollary", lower):
        return "theorem_interpretation"
    return "general_math_claim"


# ── verification prompt building ─────────────────────────────────────


def build_claim_verification_task(claim: ExtractedClaim, file_path: str) -> str:
    """Build a focused verification prompt for a single claim.

    The prompt gives the verifier:
    1. The specific claim to verify
    2. Surrounding context (definitions, equations)
    3. Instructions to write SymPy/Python to check it
    """
    return (
        f"You are verifying a specific mathematical claim from the paper at `{file_path}`.\n\n"
        f"**Source:** {claim.source_label} (line {claim.line_number})\n"
        f"**Claim type:** {claim.claim_type}\n\n"
        f"**The specific claim to verify:**\n"
        f"```\n{claim.claim_text}\n```\n\n"
        f"**Full paragraph containing the claim:**\n"
        f"```\n{claim.paragraph_text}\n```\n\n"
        f"**Relevant context (definitions, equations):**\n"
        f"```\n{claim.context}\n```\n\n"
        f"**Instructions:**\n"
        f"1. Read the paper at `{file_path}` to understand the full context if needed.\n"
        f"2. Write a Python/SymPy script to verify this claim step by step.\n"
        f"3. Run the script with Bash.\n"
        f"4. Compare the computed result with the paper's stated claim.\n"
        f"5. If the claim is correct, return an empty findings array.\n"
        f"6. If there is an error, describe it precisely.\n\n"
        f"Return JSON with a 'findings' array. Each finding needs: "
        f"category, severity, title, snippet, explanation, fix.\n"
        f"Allowed categories: math_verification, sign_error, limit_error, "
        f"algebraic_error, comparative_static_error, formula_inconsistency.\n"
        f"Allowed severities: critical, major, minor.\n"
        f'If the claim checks out, return {{"findings": []}}.'
    )


def build_claim_verifier_agent_def() -> dict[str, object]:
    """Return the Claude agent definition for focused claim verification."""
    return {
        "description": "Verifies a single mathematical claim using SymPy/Python computation.",
        "prompt": (
            "You are a mathematical claim verifier. You receive one specific claim "
            "from an academic paper and must verify it using SymPy/Python computation. "
            "Write a script, run it, and compare the result with the paper's statement. "
            "Be precise and conservative — only flag genuine errors. "
            "Return JSON with a 'findings' array. "
            "Each finding needs: category, severity, title, snippet, explanation, fix. "
            "Allowed categories: math_verification, sign_error, limit_error, "
            "algebraic_error, comparative_static_error, formula_inconsistency. "
            "Allowed severities: critical, major, minor. "
            'If the claim is correct, return {"findings": []}.'
        ),
        "tools": ["Read", "Glob", "Grep", "Bash"],
    }
