"""Benchmark and evaluation framework.

Suites: math-cases, proofnet, proofbench, processbench, refine.
Adapters for HuggingFace datasets and provenance tracking.
"""

from .framework import (
    BENCHMARK_MODES,
    BENCHMARK_SUITES,
    BenchmarkCaseRun,
    BenchmarkRoles,
    BenchmarkRun,
    parse_provider_model_spec,
    run_benchmark,
)
from .history import render_history, write_history_report
from .math_bench import run_math_benchmark
from .provenance import (
    BenchmarkProvenance,
    RegistryEntry,
    append_to_registry,
    build_provenance,
    load_registry,
)
from .refine import run_refine_benchmark
from .writing_bench import run_writing_benchmark

__all__ = [
    "BENCHMARK_MODES",
    "BENCHMARK_SUITES",
    "BenchmarkCaseRun",
    "BenchmarkProvenance",
    "BenchmarkRoles",
    "BenchmarkRun",
    "RegistryEntry",
    "append_to_registry",
    "build_provenance",
    "load_registry",
    "parse_provider_model_spec",
    "render_history",
    "run_benchmark",
    "run_math_benchmark",
    "run_refine_benchmark",
    "run_writing_benchmark",
    "write_history_report",
]
