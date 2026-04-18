"""Ingestion benchmark: evaluate parser quality on real arXiv papers.

Run with:
    pytest tests/test_ingestion_benchmark.py -v
    pytest tests/test_ingestion_benchmark.py -v --tb=no  # summary only

The benchmark evaluates 24 arXiv papers across 8 quality dimensions:
title, authors, abstract, sections, math, clean section titles,
leftover LaTeX commands, and no errors.

Papers are stored in tests/fixtures/arxiv/ with a manifest.json
describing each paper's ID, main .tex file, field, and whether it
uses multi-file \\input{} structure.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from revisica.ingestion.markdown_metrics import detect_leftover_latex_commands
from revisica.ingestion.registry import parse_document

FIXTURES = Path(__file__).parent / "fixtures" / "arxiv"
MANIFEST = FIXTURES / "manifest.json"


def _load_manifest() -> list[dict]:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def _evaluate_paper(arxiv_id: str, tex_name: str) -> dict:
    """Run ingestion pipeline on a single paper and return quality metrics."""
    tex_path = FIXTURES / arxiv_id / tex_name
    if not tex_path.exists():
        return {"id": arxiv_id, "error": f"{tex_name} not found", "skipped": True}

    doc = parse_document(tex_path)
    md = doc.markdown

    # Count math
    dollar_inline = len(re.findall(r"(?<!\$)\$(?!\$)(.+?)(?<!\$)\$(?!\$)", md))
    dollar_display = len(re.findall(r"\$\$", md)) // 2

    leftover_cmds = detect_leftover_latex_commands(md)

    # Check section titles for LaTeX remnants
    def collect_titles(sections):
        titles = []
        for s in sections:
            titles.append(s.title)
            titles.extend(collect_titles(s.children))
        return titles

    all_titles = collect_titles(doc.sections)
    dirty_titles = [t for t in all_titles if "\\" in t or "{" in t]

    def count_sections(sections):
        n = len(sections)
        for s in sections:
            n += count_sections(s.children)
        return n

    return {
        "id": arxiv_id,
        "parser": doc.parser_used,
        "title_ok": bool(doc.metadata.title)
            and "\\" not in doc.metadata.title
            and "{" not in doc.metadata.title,
        "title": doc.metadata.title[:80],
        "authors_ok": len(doc.metadata.authors) > 0,
        "abstract_ok": len(doc.metadata.abstract) > 50,
        "sections": count_sections(doc.sections),
        "has_math": dollar_inline > 0 or dollar_display > 0,
        "math_inline": dollar_inline,
        "math_display": dollar_display,
        "clean_titles": len(dirty_titles) == 0,
        "leftover_count": len(leftover_cmds),
        "md_len": len(md),
        "skipped": False,
        "error": None,
    }


# ── Collect results once per session ────────────────────────────────

_results_cache: list[dict] | None = None


def _get_results() -> list[dict]:
    global _results_cache
    if _results_cache is not None:
        return _results_cache
    manifest = _load_manifest()
    results = []
    for entry in manifest:
        try:
            r = _evaluate_paper(entry["id"], entry["tex"])
            r["field"] = entry.get("field", "")
            r["multi_file"] = entry.get("multi_file", False)
        except Exception as e:
            r = {
                "id": entry["id"],
                "error": str(e)[:200],
                "skipped": False,
                "field": entry.get("field", ""),
                "multi_file": entry.get("multi_file", False),
            }
        results.append(r)
    _results_cache = results
    return results


# ── Per-paper parametrized tests ────────────────────────────────────

_manifest_data = json.loads(MANIFEST.read_text(encoding="utf-8")) if MANIFEST.exists() else []
_paper_ids = [e["id"] for e in _manifest_data]


@pytest.fixture(scope="module")
def all_results():
    return _get_results()


def _result_for(results, arxiv_id):
    for r in results:
        if r["id"] == arxiv_id:
            return r
    pytest.skip(f"{arxiv_id} not in results")


class TestIngestionBenchmark:
    """Run ingestion on all arXiv papers and check quality metrics."""

    def test_no_parse_errors(self, all_results):
        """All papers should parse without exceptions."""
        errors = [(r["id"], r["error"]) for r in all_results if r.get("error")]
        assert not errors, f"Parse errors: {errors}"

    def test_math_extraction_rate(self, all_results):
        """At least 60% of non-multi-file papers should have math extracted."""
        single_file = [r for r in all_results if not r.get("multi_file") and not r.get("skipped")]
        with_math = [r for r in single_file if r.get("has_math")]
        rate = len(with_math) / len(single_file) if single_file else 0
        assert rate >= 0.6, (
            f"Math extraction rate {rate:.0%} ({len(with_math)}/{len(single_file)}) "
            f"below 60% threshold"
        )

    def test_section_extraction_rate(self, all_results):
        """At least 60% of non-multi-file papers should have ≥3 sections."""
        single_file = [r for r in all_results if not r.get("multi_file") and not r.get("skipped")]
        with_sections = [r for r in single_file if r.get("sections", 0) >= 3]
        rate = len(with_sections) / len(single_file) if single_file else 0
        assert rate >= 0.6, (
            f"Section extraction rate {rate:.0%} ({len(with_sections)}/{len(single_file)}) "
            f"below 60% threshold"
        )

    def test_abstract_extraction_rate(self, all_results):
        """At least 50% of papers should have abstract extracted."""
        non_skipped = [r for r in all_results if not r.get("skipped")]
        with_abstract = [r for r in non_skipped if r.get("abstract_ok")]
        rate = len(with_abstract) / len(non_skipped) if non_skipped else 0
        assert rate >= 0.5, (
            f"Abstract extraction rate {rate:.0%} ({len(with_abstract)}/{len(non_skipped)}) "
            f"below 50% threshold"
        )

    def test_multi_file_papers_flagged(self, all_results):
        """Multi-file papers with low output are a known limitation, not a bug."""
        multi = [r for r in all_results if r.get("multi_file") and not r.get("skipped")]
        low_output = [r for r in multi if r.get("md_len", 0) < 2000]
        # This is informational — multi-file papers need \input resolution
        # which tex-basic doesn't support. Pandoc handles it.
        if low_output:
            ids = [r["id"] for r in low_output]
            pytest.xfail(
                f"{len(low_output)} multi-file papers have low output "
                f"(tex-basic cannot follow \\input): {ids}"
            )


class TestIngestionBenchmarkSummary:
    """Aggregate quality report — printed as test output."""

    def test_print_summary(self, all_results, capsys):
        """Print full benchmark summary table."""
        results = all_results

        print("\n" + "=" * 85)
        print("INGESTION BENCHMARK — arXiv Papers × tex-basic parser")
        print("=" * 85)

        print(f"\n{'ID':>14s}  {'Fld':>6s}  {'MF':>2s}  {'Title':>5s}  {'Auth':>4s}  "
              f"{'Abst':>4s}  {'Sect':>4s}  {'Math':>4s}  {'CTit':>4s}  {'Left':>4s}  {'Size':>7s}")
        print("-" * 85)

        ok = lambda b: "✓" if b else "✗"
        for r in results:
            if r.get("skipped"):
                print(f"{r['id']:>14s}  {'':>6s}  {'':>2s}  SKIPPED")
                continue
            mf = "Y" if r.get("multi_file") else ""
            print(
                f"{r['id']:>14s}  {r.get('field','')[:6]:>6s}  {mf:>2s}  "
                f"{ok(r.get('title_ok')):>5s}  {ok(r.get('authors_ok')):>4s}  "
                f"{ok(r.get('abstract_ok')):>4s}  {r.get('sections',0):>4d}  "
                f"{ok(r.get('has_math')):>4s}  {ok(r.get('clean_titles')):>4s}  "
                f"{r.get('leftover_count',0):>4d}  {r.get('md_len',0):>7,d}"
            )

        n = len([r for r in results if not r.get("skipped")])
        n_single = len([r for r in results if not r.get("multi_file") and not r.get("skipped")])
        checks = {
            "Title extracted":      sum(1 for r in results if r.get("title_ok")),
            "Authors extracted":    sum(1 for r in results if r.get("authors_ok")),
            "Abstract extracted":   sum(1 for r in results if r.get("abstract_ok")),
            f"Sections ≥3":        sum(1 for r in results if r.get("sections", 0) >= 3),
            "Has math":             sum(1 for r in results if r.get("has_math")),
            "Clean section titles": sum(1 for r in results if r.get("clean_titles")),
            "No leftover cmds":     sum(1 for r in results if r.get("leftover_count", 0) == 0),
            "No errors":            sum(1 for r in results if not r.get("error")),
        }

        print(f"\n{'SUMMARY':>14s}  ({n} papers, {n_single} single-file)")
        print("-" * 50)
        total = 0
        for check, passed in checks.items():
            pct = passed / n * 100 if n else 0
            total += passed
            print(f"  {check:25s}  {passed:>2d}/{n}  ({pct:5.1f}%)")

        grand = total / (len(checks) * n) * 100 if n else 0
        print(f"\n  {'OVERALL':25s}  {total}/{len(checks) * n}  ({grand:5.1f}%)")

        print(f"\nKnown limitations:")
        print(f"  - tex-basic cannot follow \\input{{}}/\\include{{}}")
        print(f"  - Title/author extraction fails on non-standard formatting")
        print(f"  - Leftover LaTeX commands not stripped (figures, bibliography, etc.)")
        print(f"  - Install pandoc to fix most issues: brew install pandoc")

        # Always pass — this test is for the printed report
        assert True
