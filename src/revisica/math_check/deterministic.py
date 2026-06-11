from __future__ import annotations

import sympy as sp
from sympy.calculus.util import continuous_domain
from sympy.sets import Interval

from .extraction import find_variable_names, parse_expr
from .probe import (
    find_inequality_counterexample,
    numeric_integral_matches,
    prove_inequality_on_interval,
)
from .types import FunctionDefinition, MathClaim, MathIssue, ProofBlock, ProofBlueprint


def analyze_claims(
    claims: list[MathClaim],
    functions: list[FunctionDefinition],
) -> list[MathIssue]:
    issues: list[MathIssue] = []
    function_by_name = {item.name: item for item in functions}
    for claim in claims:
        try:
            issue = _check_claim(claim, function_by_name)
        except Exception:
            # Real papers contain LaTeX the parser/prober can't handle
            # (\alpha_i, \sum, ...). A claim we can't analyze must stay
            # silent — it must never crash the whole lane.
            issue = None
        if issue is not None:
            issues.append(issue)
    return issues


def _check_claim(
    claim: MathClaim,
    function_by_name: dict[str, FunctionDefinition],
) -> MathIssue | None:
    if claim.kind == "integral_equality":
        return _check_integral_claim(claim)
    if claim.kind == "average_value":
        return _check_average_value_claim(claim)
    if claim.kind == "continuity_integrability":
        return _check_continuity_claim(claim, function_by_name)
    if claim.kind == "bounded_inequality":
        return _check_bounded_inequality_claim(claim)
    return None


def analyze_blueprints(
    blueprints: list[ProofBlueprint],
    proofs: list[ProofBlock],
) -> list[MathIssue]:
    issues: list[MathIssue] = []
    matched_proof_lines = {
        blueprint.proof.line_number
        for blueprint in blueprints
        if blueprint.proof is not None
    }

    for blueprint in blueprints:
        theorem = blueprint.theorem
        if blueprint.proof is None:
            issues.append(
                MathIssue(
                    line_number=theorem.line_number,
                    status="needs-human-check",
                    severity="major",
                    title=f"{theorem.env_name.title()} statement has no adjacent proof",
                    snippet=theorem.snippet,
                    explanation="A theorem-like statement was found, but no nearby proof environment could be paired with it automatically.",
                    fix="Add a proof, or mark the statement as assumed/background material explicitly.",
                    evidence="Blueprint-lite pairing could not find a proof block after this theorem.",
                )
            )
            continue

        for obligation in blueprint.obligations:
            if _looks_like_weak_justification(obligation.text):
                issues.append(
                    MathIssue(
                        line_number=obligation.proof_line_number,
                        status="needs-human-check",
                        severity="major",
                        title="Weakly justified proof step",
                        snippet=obligation.text,
                        explanation="This proof step uses cue words like 'clearly', 'obvious', or 'therefore' and may be skipping a substantive argument.",
                        fix="Expand this step into an explicit derivation or cite the exact prior result being used.",
                        evidence=(
                            f"Extracted from {theorem.env_name} on line {theorem.line_number} as "
                            f"proof obligation {obligation.step_index}."
                        ),
                    )
                )

    for proof in proofs:
        if proof.line_number not in matched_proof_lines:
            issues.append(
                MathIssue(
                    line_number=proof.line_number,
                    status="needs-human-check",
                    severity="major",
                    title="Proof block could not be matched to a theorem-like statement",
                    snippet=proof.snippet,
                    explanation="A proof environment was found, but no preceding theorem-like statement could be paired with it safely.",
                    fix="Check theorem/proof ordering and ensure each proof is attached to a nearby theorem, lemma, or proposition.",
                    evidence="Blueprint-lite pairing did not match this proof to any theorem-like block.",
                )
            )

    return issues


def issue_sort_key(issue: MathIssue) -> tuple[int, int, int, str]:
    severity_order = {"critical": 0, "major": 1, "minor": 2, "info": 3}
    status_order = {
        "machine-refuted": 0,
        "llm-suspected": 1,
        "needs-human-check": 2,
        "machine-verified": 3,
    }
    return (
        status_order.get(issue.status, 9),
        severity_order.get(issue.severity, 9),
        issue.line_number,
        issue.title,
    )


def _check_integral_claim(claim: MathClaim) -> MathIssue | None:
    var_name = claim.details["variable"]
    variable = sp.Symbol(var_name, real=True)
    integrand = parse_expr(claim.details["integrand"], variable_names=[var_name])
    lower = parse_expr(claim.details["a"], variable_names=[var_name])
    upper = parse_expr(claim.details["b"], variable_names=[var_name])
    rhs = parse_expr(claim.details["rhs"], variable_names=[var_name])
    computed = sp.simplify(sp.integrate(integrand, (variable, lower, upper)))
    if computed.has(sp.Integral):
        # No closed form — fall back to numeric quadrature instead of
        # refuting the claim just because symbolic integration gave up.
        return _check_integral_claim_numerically(
            claim, integrand, variable, lower, upper, rhs
        )
    difference = sp.simplify(computed - rhs)
    if difference == 0:
        return MathIssue(
            line_number=claim.line_number,
            status="machine-verified",
            severity="info",
            title="Integral equality verified",
            snippet=claim.snippet,
            explanation="The definite integral matches the stated right-hand side.",
            fix="No change needed.",
            evidence=f"SymPy computed {sp.latex(computed)}.",
        )
    return MathIssue(
        line_number=claim.line_number,
        status="machine-refuted",
        severity="critical",
        title="Incorrect definite integral",
        snippet=claim.snippet,
        explanation="The stated value of the definite integral does not match the symbolic computation.",
        fix=f"Replace the stated value with `{sp.latex(computed)}` and show the derivation explicitly.",
        evidence=f"SymPy computed {sp.latex(computed)} while the draft states {sp.latex(rhs)}.",
    )


def _check_integral_claim_numerically(
    claim: MathClaim,
    integrand: sp.Expr,
    variable: sp.Symbol,
    lower: sp.Expr,
    upper: sp.Expr,
    rhs: sp.Expr,
) -> MathIssue | None:
    matches = numeric_integral_matches(integrand, variable, lower, upper, rhs)
    if matches is None:
        return MathIssue(
            line_number=claim.line_number,
            status="needs-human-check",
            severity="major",
            title="Definite integral could not be evaluated",
            snippet=claim.snippet,
            explanation="Neither symbolic integration nor numeric quadrature could settle this integral claim.",
            fix="Check the integral by hand or restate it in a form amenable to verification.",
            evidence="sympy.integrate returned an unevaluated integral and numeric evaluation failed.",
        )
    if matches:
        return MathIssue(
            line_number=claim.line_number,
            status="machine-verified",
            severity="info",
            title="Integral equality verified numerically",
            snippet=claim.snippet,
            explanation="Symbolic integration found no closed form, but numeric quadrature matches the stated value.",
            fix="No change needed.",
            evidence=(
                f"Numeric quadrature gives {sp.Integral(integrand, (variable, lower, upper)).evalf(10)}, "
                f"matching the stated {sp.latex(rhs)} within tolerance."
            ),
        )
    return MathIssue(
        line_number=claim.line_number,
        status="machine-refuted",
        severity="critical",
        title="Incorrect definite integral",
        snippet=claim.snippet,
        explanation="The stated value of the definite integral does not match numeric quadrature (no closed form exists for a symbolic check).",
        fix="Recompute the integral; the stated value is off by more than numeric tolerance.",
        evidence=(
            f"Numeric quadrature gives {sp.Integral(integrand, (variable, lower, upper)).evalf(10)} "
            f"while the draft states {sp.latex(rhs)} ≈ {sp.sympify(rhs).evalf(10)}."
        ),
    )


def _check_bounded_inequality_claim(claim: MathClaim) -> MathIssue | None:
    var_name = claim.details["variable"]
    variable = sp.Symbol(var_name, real=True)
    relation = claim.details["relation"]
    lhs = parse_expr(claim.details["lhs"], variable_names=[var_name])
    rhs = parse_expr(claim.details["rhs"], variable_names=[var_name])
    lower = parse_expr(claim.details["a"], variable_names=[var_name])
    upper = parse_expr(claim.details["b"], variable_names=[var_name])

    witness = find_inequality_counterexample(lhs, rhs, relation, variable, lower, upper)
    if witness is not None:
        return MathIssue(
            line_number=claim.line_number,
            status="machine-refuted",
            severity="critical",
            title="Inequality fails on the stated interval",
            snippet=claim.snippet,
            explanation="The claimed inequality has an exact counterexample inside the quantified interval.",
            fix="Restrict the interval, weaken the inequality, or correct the bound.",
            evidence=witness.describe(variable, relation),
        )

    proven = prove_inequality_on_interval(lhs, rhs, relation, variable, lower, upper)
    if proven:
        return MathIssue(
            line_number=claim.line_number,
            status="machine-verified",
            severity="info",
            title="Inequality verified on the stated interval",
            snippet=claim.snippet,
            explanation="The inequality holds across the quantified interval according to symbolic extremum analysis.",
            fix="No change needed.",
            evidence=(
                f"The minimum of the inequality gap over [{lower}, {upper}] is "
                f"{'positive' if relation in ('<', '>') else 'non-negative'}, "
                f"and grid sampling found no counterexample."
            ),
        )
    # Sampling found nothing and the symbolic proof is inconclusive —
    # stay quiet rather than emit a low-confidence verdict.
    return None


def _check_average_value_claim(claim: MathClaim) -> MathIssue | None:
    variable_names = find_variable_names(claim.details["expr"])
    variable = sp.Symbol(variable_names[0], real=True) if variable_names else sp.Symbol("x", real=True)
    expr = parse_expr(claim.details["expr"], variable_names=[str(variable)])
    lower = parse_expr(claim.details["a"], variable_names=[str(variable)])
    upper = parse_expr(claim.details["b"], variable_names=[str(variable)])
    rhs = parse_expr(claim.details["rhs"], variable_names=[str(variable)])
    computed = sp.simplify(sp.integrate(expr, (variable, lower, upper)) / (upper - lower))
    difference = sp.simplify(computed - rhs)
    if difference == 0:
        return MathIssue(
            line_number=claim.line_number,
            status="machine-verified",
            severity="info",
            title="Average value claim verified",
            snippet=claim.snippet,
            explanation="The stated average value matches the symbolic computation.",
            fix="No change needed.",
            evidence=f"SymPy computed the average value as {sp.latex(computed)}.",
        )
    return MathIssue(
        line_number=claim.line_number,
        status="machine-refuted",
        severity="critical",
        title="Incorrect average value",
        snippet=claim.snippet,
        explanation="The stated average value does not match the average-value formula applied to the expression and interval.",
        fix=f"Replace the stated value with `{sp.latex(computed)}` and show the formula `(1/(b-a))∫_a^b f(x)dx`.",
        evidence=f"SymPy computed the average value as {sp.latex(computed)} while the draft states {sp.latex(rhs)}.",
    )


def _check_continuity_claim(
    claim: MathClaim,
    function_by_name: dict[str, FunctionDefinition],
) -> MathIssue | None:
    function = function_by_name.get(claim.details["function_name"])
    if function is None:
        return MathIssue(
            line_number=claim.line_number,
            status="needs-human-check",
            severity="major",
            title="Unable to bind continuity claim to a function definition",
            snippet=claim.snippet,
            explanation="The draft makes a continuity claim, but the checker could not identify the underlying function robustly.",
            fix="Inspect the surrounding equations manually.",
            evidence="No matching function definition was available.",
        )
    if function.expression is None:
        return MathIssue(
            line_number=claim.line_number,
            status="needs-human-check",
            severity="major",
            title="Continuity claim references a function known only by type signature",
            snippet=claim.snippet,
            explanation="The function was declared via a type signature (e.g. f: X → Y) without a closed-form expression, so continuity cannot be verified symbolically.",
            fix="Provide the explicit definition of the function or check continuity manually.",
            evidence=f"Function '{function.name}' has no parsed expression; signature recorded as {function.expression_text!r}.",
        )

    variable = sp.Symbol(function.variable, real=True)
    lower = parse_expr(claim.details["a"], variable_names=[function.variable])
    upper = parse_expr(claim.details["b"], variable_names=[function.variable])
    interval = Interval(lower, upper)
    domain = continuous_domain(function.expression, variable, sp.S.Reals)
    if interval.is_subset(domain):
        return MathIssue(
            line_number=claim.line_number,
            status="machine-verified",
            severity="info",
            title="Continuity claim verified on the stated interval",
            snippet=claim.snippet,
            explanation="The function is continuous on the stated interval according to symbolic domain analysis.",
            fix="No change needed.",
            evidence=f"Continuous domain over the reals is {domain}.",
        )

    return MathIssue(
        line_number=claim.line_number,
        status="machine-refuted",
        severity="critical",
        title="False continuity or safe-integrability claim",
        snippet=claim.snippet,
        explanation="The function is not continuous on the stated closed interval, so the paper's claim that it can be safely integrated there is not justified.",
        fix="Either change the interval to avoid singularities, remove the claim, or rewrite the passage as an improper-integral discussion.",
        evidence=f"Continuous domain over the reals is {domain}, which does not contain the full interval {interval}.",
    )


def _looks_like_weak_justification(text: str) -> bool:
    lowered = text.lower()
    weak_markers = (
        "clearly",
        "obvious",
        "obviously",
        "trivial",
        "trivially",
        "immediate",
        "immediately",
        "it follows",
        "therefore",
        "hence",
        "thus",
    )
    return any(marker in lowered for marker in weak_markers)
