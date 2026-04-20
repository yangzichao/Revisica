"""Task-model auto-routing for Revisica.

When a ProviderModelSpec has no explicit model, this module selects an
appropriate model based on the task category. The defaults should stay
compatible with the provider account actually running the agent, not an
idealized model menu.

The defaults are conservative — they only kick in when no model is
explicitly specified.  Users can always override via --reviewer-a, etc.
"""
from __future__ import annotations

from .core_types import ProviderModelSpec


# ── task categories ──────────────────────────────────────────────────

TASK_MATH_REASONING = "math-reasoning"
TASK_MATH_SELF_CHECK = "math-self-check"
TASK_MATH_ADJUDICATION = "math-adjudication"
TASK_WRITING_BASIC = "writing-basic"
TASK_WRITING_STRUCTURE = "writing-structure"
TASK_WRITING_VENUE = "writing-venue"
TASK_WRITING_SELF_CHECK = "writing-self-check"
TASK_WRITING_JUDGE = "writing-judge"
TASK_MATH_CLAIM_VERIFY = "math-claim-verify"
TASK_NOTATION_TRACK = "notation-track"
TASK_FORMULA_CROSS_CHECK = "formula-cross-check"
TASK_SECTION_CROSS_CHECK = "section-cross-check"
TASK_POLISH = "polish"


# ── role → task category mapping ─────────────────────────────────────

ROLE_TASK_MAP: dict[str, str] = {
    "proof-reviewer": TASK_MATH_REASONING,
    "self-checker": TASK_MATH_SELF_CHECK,
    "adjudicator": TASK_MATH_ADJUDICATION,
    "basic": TASK_WRITING_BASIC,
    "structure": TASK_WRITING_STRUCTURE,
    "venue": TASK_WRITING_VENUE,
    "writing-self-checker": TASK_WRITING_SELF_CHECK,
    "judge": TASK_WRITING_JUDGE,
    "math-claim-verifier": TASK_MATH_CLAIM_VERIFY,
    "notation-tracker": TASK_NOTATION_TRACK,
    "formula-cross-checker": TASK_FORMULA_CROSS_CHECK,
    "section-cross-checker": TASK_SECTION_CROSS_CHECK,
    "polish": TASK_POLISH,
}


# ── default model routes per provider ────────────────────────────────
#
# For Codex, route to models that are both strong and broadly supported by
# the current account setup. We intentionally avoid older unsupported routes
# like `o3` and `gpt-4.1`, which caused real benchmark runs to fail.
#
# These are suggestions. Users can still override them explicitly.

_GPT_ROUTES: dict[str, str] = {
    TASK_MATH_REASONING: "gpt-5",
    TASK_MATH_SELF_CHECK: "gpt-5",
    TASK_MATH_ADJUDICATION: "gpt-5",
    TASK_MATH_CLAIM_VERIFY: "gpt-5",
    TASK_WRITING_BASIC: "gpt-5",
    TASK_WRITING_STRUCTURE: "gpt-5",
    TASK_WRITING_VENUE: "gpt-5",
    TASK_WRITING_SELF_CHECK: "gpt-5",
    TASK_WRITING_JUDGE: "gpt-5",
    TASK_NOTATION_TRACK: "gpt-5",
    TASK_FORMULA_CROSS_CHECK: "gpt-5",
    TASK_SECTION_CROSS_CHECK: "gpt-5",
    # Polish: no hard-coded default — let Codex use the user's config default.
    # Rationale: gpt-5 is not available on all Codex accounts (e.g. ChatGPT
    # subscription accounts only expose gpt-5.4), and polish is tolerant of
    # any modern model.
}

_CLAUDE_ROUTES: dict[str, str] = {
    # Reasoning tasks → opus (strongest reasoning)
    TASK_MATH_REASONING: "opus",
    TASK_MATH_SELF_CHECK: "opus",
    TASK_MATH_ADJUDICATION: "opus",
    TASK_MATH_CLAIM_VERIFY: "opus",
    # Writing tasks → sonnet (fast, strong at language)
    TASK_WRITING_BASIC: "sonnet",
    TASK_WRITING_STRUCTURE: "sonnet",
    TASK_WRITING_VENUE: "sonnet",
    TASK_WRITING_SELF_CHECK: "opus",
    TASK_WRITING_JUDGE: "sonnet",
    # Cross-checks
    TASK_NOTATION_TRACK: "opus",
    TASK_FORMULA_CROSS_CHECK: "opus",
    TASK_SECTION_CROSS_CHECK: "sonnet",
    TASK_POLISH: "sonnet",
}

_ANTHROPIC_API_ROUTES: dict[str, str] = {
    TASK_MATH_REASONING: "claude-sonnet-4-20250514",
    TASK_MATH_SELF_CHECK: "claude-sonnet-4-20250514",
    TASK_MATH_ADJUDICATION: "claude-sonnet-4-20250514",
    TASK_MATH_CLAIM_VERIFY: "claude-sonnet-4-20250514",
    TASK_WRITING_BASIC: "claude-sonnet-4-20250514",
    TASK_WRITING_STRUCTURE: "claude-sonnet-4-20250514",
    TASK_WRITING_VENUE: "claude-sonnet-4-20250514",
    TASK_WRITING_SELF_CHECK: "claude-sonnet-4-20250514",
    TASK_WRITING_JUDGE: "claude-sonnet-4-20250514",
    TASK_NOTATION_TRACK: "claude-sonnet-4-20250514",
    TASK_FORMULA_CROSS_CHECK: "claude-sonnet-4-20250514",
    TASK_SECTION_CROSS_CHECK: "claude-sonnet-4-20250514",
    TASK_POLISH: "claude-sonnet-4-20250514",
}

_OPENAI_API_ROUTES: dict[str, str] = {
    TASK_MATH_REASONING: "gpt-4o",
    TASK_MATH_SELF_CHECK: "gpt-4o",
    TASK_MATH_ADJUDICATION: "gpt-4o",
    TASK_MATH_CLAIM_VERIFY: "gpt-4o",
    TASK_WRITING_BASIC: "gpt-4o",
    TASK_WRITING_STRUCTURE: "gpt-4o",
    TASK_WRITING_VENUE: "gpt-4o",
    TASK_WRITING_SELF_CHECK: "gpt-4o",
    TASK_WRITING_JUDGE: "gpt-4o",
    TASK_NOTATION_TRACK: "gpt-4o",
    TASK_FORMULA_CROSS_CHECK: "gpt-4o",
    TASK_SECTION_CROSS_CHECK: "gpt-4o",
    TASK_POLISH: "gpt-4o",
}

_DEFAULT_ROUTES: dict[str, dict[str, str]] = {
    # CLI providers (backwards-compatible names)
    "codex": _GPT_ROUTES,
    "claude": _CLAUDE_ROUTES,
    # New provider names
    "codex-cli": _GPT_ROUTES,
    "claude-cli": _CLAUDE_ROUTES,
    "anthropic-api": _ANTHROPIC_API_ROUTES,
    "openai-api": _OPENAI_API_ROUTES,
}


def resolve_model_for_task(
    spec: ProviderModelSpec,
    task_type: str,
) -> ProviderModelSpec:
    """Return a spec with an auto-selected model if none was explicitly set.

    If the spec already has a model, it is returned unchanged.
    """
    if spec.model is not None:
        return spec
    routes = _DEFAULT_ROUTES.get(spec.provider, {})
    model = routes.get(task_type)
    if model is not None:
        return ProviderModelSpec(provider=spec.provider, model=model)
    return spec


def resolve_model_for_role(
    spec: ProviderModelSpec,
    role: str,
) -> ProviderModelSpec:
    """Convenience wrapper — looks up the task type from a role name."""
    task_type = ROLE_TASK_MAP.get(role)
    if task_type is None:
        return spec
    return resolve_model_for_task(spec, task_type)
