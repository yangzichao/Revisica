"""Tests for the unified findings pipeline: collect → anchor → persist."""

from __future__ import annotations

import json
from pathlib import Path

from revisica.core_types import ReviewResult
from revisica.findings import (
    collect_unified_findings,
    load_findings_payload,
    normalize_severity,
    resolve_anchors,
    write_findings_artifacts,
)
from revisica.findings.collect import _from_math_issue
from revisica.findings.types import FindingAnchor, UnifiedFinding
from revisica.ingestion.types import DocumentSection
from revisica.math_check.types import MathIssue
from revisica.writing.types import WritingRoleArtifact

DOCUMENT = """# Sample Paper

## Introduction

We study the effect of treatment on outcomes. The estimator is
consistent under standard regularity conditions.

## Model

Let $f(x) = x^2$ for all $x$. We claim that the integral of f over
[0, 1] equals 1/2, which is incorrect on purpose.

## Conclusion

The results suggests that treatment matters.
"""

SECTIONS = [
    DocumentSection(
        id="sec-0-sample-paper",
        title="Sample Paper",
        level=1,
        start_line=0,
        end_line=15,
        content="",
        children=[
            DocumentSection(
                id="sec-1-introduction",
                title="Introduction",
                level=2,
                start_line=2,
                end_line=6,
                content="",
                children=[],
            ),
            DocumentSection(
                id="sec-2-model",
                title="Model",
                level=2,
                start_line=7,
                end_line=11,
                content="",
                children=[],
            ),
            DocumentSection(
                id="sec-3-conclusion",
                title="Conclusion",
                level=2,
                start_line=12,
                end_line=15,
                content="",
                children=[],
            ),
        ],
    ),
]


def make_finding(quote: str, line_number: int | None = None, severity: str = "major") -> UnifiedFinding:
    return UnifiedFinding(
        id="",
        lane="writing",
        role="basic",
        provider="claude",
        model=None,
        category="grammar",
        severity=severity,
        title="t",
        explanation="e",
        fix="f",
        evidence="",
        status=None,
        anchor=FindingAnchor(quote=quote, line_number=line_number),
    )


class TestAnchorResolution:
    def test_exact_quote_match(self):
        finding = make_finding("The results suggests that treatment matters.")
        resolve_anchors([finding], DOCUMENT, SECTIONS)
        anchor = finding.anchor
        assert anchor.resolution == "exact"
        assert DOCUMENT[anchor.start_offset : anchor.end_offset] == (
            "The results suggests that treatment matters."
        )
        assert anchor.section_id == "sec-3-conclusion"

    def test_quote_match_is_whitespace_insensitive(self):
        finding = make_finding("The estimator is\n   consistent under standard")
        resolve_anchors([finding], DOCUMENT, SECTIONS)
        anchor = finding.anchor
        assert anchor.resolution == "exact"
        assert DOCUMENT[anchor.start_offset : anchor.end_offset].startswith(
            "The estimator is\nconsistent"
        )
        assert anchor.section_id == "sec-1-introduction"

    def test_unmatched_quote_falls_back_to_line(self):
        finding = make_finding("this text appears nowhere in the document", line_number=10)
        resolve_anchors([finding], DOCUMENT, SECTIONS)
        anchor = finding.anchor
        assert anchor.resolution == "line"
        assert anchor.line_number == 10
        line_text = DOCUMENT[anchor.start_offset : anchor.end_offset]
        assert line_text == DOCUMENT.splitlines()[9]
        assert anchor.section_id == "sec-2-model"

    def test_no_quote_no_line_is_unresolved(self):
        finding = make_finding("")
        resolve_anchors([finding], DOCUMENT, SECTIONS)
        assert finding.anchor.resolution == "unresolved"
        assert finding.anchor.start_offset is None
        assert finding.anchor.section_id is None

    def test_out_of_range_line_is_unresolved(self):
        finding = make_finding("nope", line_number=999)
        resolve_anchors([finding], DOCUMENT, SECTIONS)
        assert finding.anchor.resolution == "unresolved"

    def test_multiline_quote_falls_back_to_longest_line(self):
        quote = "totally invented preamble line\nconsistent under standard regularity conditions."
        finding = make_finding(quote)
        resolve_anchors([finding], DOCUMENT, SECTIONS)
        anchor = finding.anchor
        assert anchor.resolution == "exact"
        assert DOCUMENT[anchor.start_offset : anchor.end_offset] == (
            "consistent under standard regularity conditions."
        )

    def test_repeated_quote_picks_occurrence_nearest_hint_line(self):
        doc = "alpha beta gamma\nfiller\nfiller\nalpha beta gamma\n"
        finding = make_finding("alpha beta gamma", line_number=4)
        resolve_anchors([finding], doc, [])
        assert finding.anchor.line_number == 4

    def test_findings_sorted_in_document_order_with_unresolved_last(self):
        late = make_finding("The results suggests that treatment matters.")
        unresolved = make_finding("")
        early = make_finding("We study the effect of treatment")
        findings = [late, unresolved, early]
        resolve_anchors(findings, DOCUMENT, SECTIONS)
        assert findings[0] is early
        assert findings[1] is late
        assert findings[2] is unresolved
        assert [finding.id for finding in findings] == ["f-001", "f-002", "f-003"]


class TestCollect:
    def _writing_artifact(self, findings: list[dict] | None) -> WritingRoleArtifact:
        result = ReviewResult(
            provider="claude",
            model=None,
            command=[],
            returncode=0,
            output="",
            stderr="",
        )
        return WritingRoleArtifact(
            role="basic", provider="claude", model=None, result=result, findings=findings
        )

    def test_collects_writing_and_math(self):
        writing_run = type(
            "W",
            (),
            {
                "artifacts": [
                    self._writing_artifact(
                        [
                            {
                                "category": "grammar",
                                "severity": "minor",
                                "title": "Agreement",
                                "snippet": "The results suggests",
                                "explanation": "x",
                                "fix": "The results suggest",
                            },
                            "not-a-dict-is-skipped",
                        ]
                    )
                ]
            },
        )()
        math_run = type(
            "M",
            (),
            {
                "issues": [
                    MathIssue(
                        line_number=11,
                        status="machine-refuted",
                        severity="critical",
                        title="Integral mismatch",
                        snippet="the integral of f over",
                        explanation="integral is 1/3",
                        fix="replace 1/2 with 1/3",
                        evidence="sympy: integrate(x**2, (x, 0, 1)) == 1/3",
                    )
                ]
            },
        )()

        findings = collect_unified_findings(writing_run, math_run)
        assert len(findings) == 2
        lanes = {finding.lane for finding in findings}
        assert lanes == {"writing", "math"}
        math_finding = next(f for f in findings if f.lane == "math")
        assert math_finding.role == "deterministic"
        assert math_finding.status == "machine-refuted"
        assert math_finding.anchor.line_number == 11

    def test_handles_none_runs(self):
        assert collect_unified_findings(None, None) == []

    def test_llm_status_maps_to_llm_proof_role(self):
        issue = MathIssue(
            line_number=3,
            status="llm-suspected",
            severity="major",
            title="t",
            snippet="s",
            explanation="e",
            fix="f",
            evidence="",
        )
        assert _from_math_issue(issue).role == "llm-proof"


class TestSeverityNormalization:
    def test_known_levels_pass_through(self):
        for level in ("critical", "major", "minor", "info"):
            assert normalize_severity(level) == level

    def test_aliases_and_unknowns(self):
        assert normalize_severity("HIGH") == "critical"
        assert normalize_severity("warning") == "major"
        assert normalize_severity("nit") == "minor"
        assert normalize_severity(None) == "major"
        assert normalize_severity("weird-thing") == "major"


class TestPersistence:
    def test_round_trip(self, tmp_path: Path):
        finding = make_finding("We study the effect of treatment")
        resolve_anchors([finding], DOCUMENT, SECTIONS)
        write_findings_artifacts(tmp_path, [finding], DOCUMENT)

        raw = json.loads((tmp_path / "findings.json").read_text(encoding="utf-8"))
        assert raw["count"] == 1
        assert raw["findings"][0]["anchor"]["resolution"] == "exact"

        payload = load_findings_payload(tmp_path)
        assert payload is not None
        assert payload["document_markdown"] == DOCUMENT
        anchor = payload["findings"][0]["anchor"]
        assert DOCUMENT[anchor["start_offset"] : anchor["end_offset"]] == (
            "We study the effect of treatment"
        )

    def test_missing_artifact_returns_none(self, tmp_path: Path):
        assert load_findings_payload(tmp_path) is None

    def test_corrupt_artifact_returns_none(self, tmp_path: Path):
        (tmp_path / "findings.json").write_text("{not json", encoding="utf-8")
        assert load_findings_payload(tmp_path) is None
