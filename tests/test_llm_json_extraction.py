"""Recovery of JSON objects from real-world LLM output shapes."""

from __future__ import annotations

from revisica.eval.refine import _parse_judge_output
from revisica.llm_output import extract_json_object
from revisica.math_llm.parse import extract_findings_payload as extract_math_findings
from revisica.writing.findings import extract_findings_payload as extract_writing_findings


def test_prose_then_fenced_block():
    output = (
        "The verification is complete. The assumption structure is sound.\n\n"
        '```json\n{"findings": []}\n```\n'
    )
    assert extract_writing_findings(output) == []
    assert extract_math_findings(output) == []


def test_single_backslash_latex_inside_fenced_json():
    # Shape of benchmarks/runs/prmbench-single-agent-20260413-041546/
    # counterfactual_prm_test_p2_193: `\{` and `\pi` written unescaped.
    output = (
        "```json\n"
        '{"findings": [{"step_index": 3, "status": "pass", '
        '"verdict": "The roots are $\\{e^{2\\pi ik/n} : k = 0, \\ldots, n-1\\}$."}]}\n'
        "```\n\n"
        "**Summary:** the answer is $\\mathbf{6}$, not 5."
    )
    findings = extract_math_findings(output)
    assert findings is not None
    assert findings[0]["verdict"] == "The roots are $\\{e^{2\\pi ik/n} : k = 0, \\ldots, n-1\\}$."


def test_unclosed_fence_after_latex_prose():
    # Shape of benchmarks/runs/pb-v4-opus-20260412-092726/math_6: braces in
    # the prose before the JSON and no closing fence after it.
    output = (
        "We need $(2y+3)(3y^2+cy+\\frac{5}{2}c) + R$. The remainder is 23.\n\n"
        "```json\n"
        '{\n  "findings": [\n    {"step_index": 25, "status": "error"}\n  ],\n'
        '  "summary": {"verdict": "incorrect"}\n}'
    )
    assert extract_math_findings(output) == [{"step_index": 25, "status": "error"}]


def test_non_object_json_in_bare_fence_does_not_crash():
    output = (
        "I ran the SymPy check:\n```\n[0.5, 0.25]\n```\nand also\n```\nnull\n```\n"
        '```json\n{"findings": [{"title": "Sign error"}]}\n```'
    )
    assert extract_writing_findings(output) == [{"title": "Sign error"}]


def test_top_level_array_or_null_returns_none():
    for output in ('[{"title": "x"}]', "null", "0.5"):
        assert extract_writing_findings(output) is None
        assert extract_math_findings(output) is None


def test_findings_must_be_a_list():
    assert extract_writing_findings('{"findings": null}') is None
    assert extract_math_findings('{"findings": "none"}') is None


def test_skips_objects_without_the_key_and_keeps_looking():
    output = (
        'Plan: {"step": 1}\n'
        '```json\n{"summary": "draft"}\n```\n'
        'Final: {"findings": [{"title": "Missing assumption"}]} done.'
    )
    assert extract_writing_findings(output) == [{"title": "Missing assumption"}]


def test_truncated_json_returns_none():
    output = '```json\n{"findings": [{"title": "Cut off mid'
    assert extract_writing_findings(output) is None
    assert extract_math_findings(output) is None


def test_repair_keeps_valid_escapes():
    output = '{"findings": [{"detail": "path C:\\\\tmp, set \\{x\\}\\nnext line \\u00e9"}]}'
    payload = extract_json_object(output, "findings", list)
    assert payload is not None
    assert payload["findings"][0]["detail"] == "path C:\\tmp, set \\{x\\}\nnext line \u00e9"


def test_strict_json_is_not_rewritten():
    # `\t` and `\n` are valid escapes; strict parsing wins and keeps them.
    payload = extract_json_object('{"findings": [], "note": "a\\tb"}', "findings")
    assert payload == {"findings": [], "note": "a\tb"}


def test_judge_output_with_prose():
    output = (
        "Here is my evaluation.\n"
        '{"evaluations": [{"id": "c1", "status": "matched"}, "stray"]}\n'
        "Let me know if you need more."
    )
    assert _parse_judge_output(output) == [{"id": "c1", "status": "matched"}]


def test_empty_output():
    assert extract_writing_findings("") is None
    assert extract_math_findings("   ") is None
    assert _parse_judge_output("") is None


def test_deeply_nested_output_does_not_crash():
    output = "[" * 100_000 + '{"findings": []}'
    assert extract_writing_findings(output) == []
