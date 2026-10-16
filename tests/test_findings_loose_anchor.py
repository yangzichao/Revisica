"""Loose anchoring: real reviewer quotes that do not match verbatim.

The documents and quotes come from real runs: a MinerU-ingested PDF of
``examples/minimal_paper.tex`` reviewed by claude:haiku, and a Pandoc
ingestion of ``examples/proof_blueprint_demo.tex`` reviewed by Codex and
Claude. Before the loose tier, every quote below ended up ``unresolved``.
"""

from __future__ import annotations

from revisica.findings import resolve_anchors
from revisica.findings.types import FindingAnchor, UnifiedFinding

MINERU_DOCUMENT = """# A Very Small Example Paper

Revisica Demo

# 1 Introduction

This paper studies a very important problem and it is obviously useful for many applications. We will prove a theorem very quickly and the explanation is not very precise.

# 2 Main Result

Let $f(x) = x^{2}$ . We claim that

$$
\\int_ {0} ^ {1} x ^ {2} d x = \\frac {1}{2}.
$$

Therefore, the average value of $x^{2}$ on $[0,1]$ is also $1/2$ .

Now define

$$
g (x) = \\frac {1}{x - 1}.
$$

This function is continuous on $[0,1]$ so we can safely integrate it on this interval.

# 3 Conclusion

We have shown the theorem and every step is straightforward.
"""

PANDOC_DOCUMENT = """::: theorem
**Theorem 1**. *We have $$\\int_0^1 x^2 \\, dx = \\frac{1}{2}.$$*
:::

::: proof
*Proof.* Clearly, the antiderivative of $x^2$ is $x^2/2$. Therefore $$\\int_0^1 x^2 \\, dx = \\frac{1}{2}.$$ Thus the theorem follows. ◻
:::
"""


def make_finding(quote: str, line_number: int | None = None) -> UnifiedFinding:
    return UnifiedFinding(
        id="",
        lane="writing",
        role="formula-cross-checker",
        provider="claude",
        model="haiku",
        category="math",
        severity="major",
        title="t",
        explanation="",
        fix="",
        evidence="",
        status=None,
        anchor=FindingAnchor(quote=quote, line_number=line_number),
    )


def resolve_one(quote: str, document: str, line_number: int | None = None) -> FindingAnchor:
    finding = make_finding(quote, line_number)
    resolve_anchors([finding], document)
    return finding.anchor


def anchored_text(anchor: FindingAnchor, document: str) -> str:
    assert anchor.start_offset is not None and anchor.end_offset is not None
    return document[anchor.start_offset : anchor.end_offset]


def test_verbatim_quote_stays_exact() -> None:
    anchor = resolve_one("We have shown the theorem and every step is straightforward.", MINERU_DOCUMENT)

    assert anchor.resolution == "exact"


def test_respaced_latex_matches_loosely() -> None:
    anchor = resolve_one("$$\\int_{0}^{1} x^{2}\\,dx = \\frac{1}{2}.$$", MINERU_DOCUMENT)

    assert anchor.resolution == "loose"
    assert anchored_text(anchor, MINERU_DOCUMENT) == "\\int_ {0} ^ {1} x ^ {2} d x = \\frac {1}{2}."
    assert anchor.line_number == 14


def test_ellipsis_stitched_quote_spans_both_passages() -> None:
    quote = (
        "$$g(x) = \\frac{1}{x - 1}.$$ ... \"This function is continuous on $[0,1]$ "
        "so we can safely integrate it on this interval.\""
    )

    anchor = resolve_one(quote, MINERU_DOCUMENT)

    assert anchor.resolution == "loose"
    text = anchored_text(anchor, MINERU_DOCUMENT)
    assert text.startswith("g (x) = \\frac {1}{x - 1}.")
    assert text.endswith("safely integrate it on this interval.")


def test_quote_wrapped_in_quote_marks_matches_inner_text() -> None:
    sentence = "This paper studies a very important problem and it is obviously useful for many applications."

    anchor = resolve_one(f'"{sentence}"', MINERU_DOCUMENT)

    assert anchor.resolution == "loose"
    assert anchored_text(anchor, MINERU_DOCUMENT) == sentence


def test_labelled_quotes_in_different_sections_anchor_the_first_only() -> None:
    quote = (
        'Section 2: $$\\int_{0}^{1} x^{2}\\,dx = \\frac{1}{2}.$$ and "the average value of '
        '$x^{2}$ on $[0,1]$ is also $1/2$". Section 3: "We have shown the theorem"'
    )

    anchor = resolve_one(quote, MINERU_DOCUMENT)

    assert anchor.resolution == "loose"
    text = anchored_text(anchor, MINERU_DOCUMENT)
    assert text.endswith("is also $1/2")
    # The "# 3 Conclusion" heading separates the passages; do not span it.
    assert "Conclusion" not in text


def test_quote_without_math_delimiters_matches() -> None:
    anchor = resolve_one("Therefore \\int_0^1 x^2 \\, dx = \\frac{1}{2}.", PANDOC_DOCUMENT)

    assert anchor.resolution == "loose"
    assert anchored_text(anchor, PANDOC_DOCUMENT).startswith("Therefore $$\\int_0^1")
    assert anchor.line_number == 6


def test_label_before_full_width_colon_is_ignored() -> None:
    quote = "Theorem (line 12) 和 Proof (line 20) 都写了：\\int_0^1 x^2 \\, dx = \\frac{1}{2}."

    anchor = resolve_one(quote, PANDOC_DOCUMENT)

    assert anchor.resolution == "loose"
    assert anchored_text(anchor, PANDOC_DOCUMENT) == "\\int_0^1 x^2 \\, dx = \\frac{1}{2}."


def test_repeated_fragment_picks_occurrence_nearest_hint_line() -> None:
    quote = "Lines 12 and 20: \\int_0^1 x^2\\,dx = \\frac{1}{2}"

    anchor = resolve_one(quote, PANDOC_DOCUMENT, line_number=6)

    assert anchor.resolution == "loose"
    assert anchor.line_number == 6


def test_only_short_fragments_falls_back_to_line() -> None:
    anchor = resolve_one('"We claim" ... "Revisica"', MINERU_DOCUMENT, line_number=11)

    assert anchor.resolution == "line"
    assert anchor.line_number == 11


def test_fragments_far_apart_anchor_the_first_only() -> None:
    filler = "Filler sentence that pads the paragraph out. " * 10
    document = f"The first passage sits right here.\n\n{filler}\n\nThe second passage is far away.\n"

    anchor = resolve_one("The first passage sits right here ... The second passage is far away", document)

    assert anchor.resolution == "loose"
    assert anchored_text(anchor, document) == "The first passage sits right here"
