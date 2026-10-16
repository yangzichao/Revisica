"""Deterministic math checks on ingested Markdown, not just raw .tex.

``revisica review`` runs the math lane on the ingested Markdown. Before:

- claim extraction only matched ``\\[ ... \\]``, but Pandoc, tex-basic and
  MinerU all write display math as ``$$ ... $$``, so the wrong integral in
  ``examples/minimal_paper.tex`` was never checked;
- MinerU spaces LaTeX out (``g (x) = \\frac {1}{x - 1}``), so ``g`` was
  dropped and "This function is continuous on [0,1]" bound to
  ``f = x^2`` — reported as *machine-verified*.
"""

from __future__ import annotations

from pathlib import Path

from revisica.math_check.extraction import extract_functions, extract_math_claims, normalize_latex
from revisica.math_review import review_math_file

_EXAMPLE_PAPER = Path(__file__).resolve().parents[1] / "examples" / "minimal_paper.tex"

# What Pandoc and tex-basic produce for minimal_paper.tex (abridged).
PANDOC_MARKDOWN = """# Main Result

Let $f(x) = x^2$. We claim that $$\\int_0^1 x^2 \\, dx = \\frac{1}{2}.$$
Therefore, the average value of $x^2$ on $[0,1]$ is also $1/2$.

Now define $$g(x) = \\frac{1}{x-1}.$$ This function is continuous on $[0,1]$ so we can safely integrate it on this interval.
"""

# MinerU output for the PDF of minimal_paper.tex (abridged).
MINERU_MARKDOWN = """# 2 Main Result

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
"""


def claim_kinds(content: str) -> list[str]:
    return sorted(claim.kind for claim in extract_math_claims(content, extract_functions(content)))


def issue_statuses(content: str, tmp_path: Path) -> list[str]:
    run = review_math_file(str(_EXAMPLE_PAPER), output_dir=str(tmp_path), content_override=content)
    return sorted(issue.status for issue in run.issues)


def test_display_math_in_dollar_form_yields_the_integral_claim() -> None:
    assert claim_kinds(PANDOC_MARKDOWN) == ["average_value", "continuity_integrability", "integral_equality"]


def test_pandoc_markdown_refutes_the_same_claims_as_raw_tex(tmp_path: Path) -> None:
    raw_tex_statuses = issue_statuses(_EXAMPLE_PAPER.read_text(encoding="utf-8"), tmp_path / "tex")

    assert issue_statuses(PANDOC_MARKDOWN, tmp_path / "pandoc") == raw_tex_statuses
    assert raw_tex_statuses == ["machine-refuted"] * 3


def test_mineru_spacing_still_parses_the_definition() -> None:
    functions = {function.name: function for function in extract_functions(MINERU_MARKDOWN)}

    assert set(functions) == {"f", "g"}
    assert str(functions["g"].expression) == "1/(x - 1)"


def test_mineru_markdown_refutes_instead_of_verifying(tmp_path: Path) -> None:
    assert issue_statuses(MINERU_MARKDOWN, tmp_path) == ["machine-refuted"] * 3


def test_continuity_claim_is_not_bound_past_an_unparseable_definition() -> None:
    content = (
        "Let $f(x) = x^2$.\n\n"
        "Now define $$g(x) = \\mathcal{Q}\\{1\\}.$$\n"
        "This function is continuous on $[0,1]$ so we can safely integrate it on this interval.\n"
    )

    claims = extract_math_claims(content, extract_functions(content))

    assert [claim.kind for claim in claims] == []


def test_dollar_display_inequality_is_extracted() -> None:
    content = "$$x^3 \\le 2x \\quad \\text{for all } x \\in [0,2]$$\n"

    claims = extract_math_claims(content, [])

    assert [(claim.kind, claim.details["relation"]) for claim in claims] == [("bounded_inequality", "<=")]


def test_normalize_latex_closes_parser_spacing() -> None:
    assert normalize_latex("\\int_ {0} ^ {1} x ^ {2} d x = \\frac {1}{2}.") == "\\int_{0}^{1} x^{2} d x = \\frac{1}{2}."
