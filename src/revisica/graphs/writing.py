"""Writing review subgraph — 5-node pipeline.

bootstrap_and_extract → run_parallel_roles → run_self_checks → run_judge → write_summary → END
"""

from __future__ import annotations

import functools

from langgraph.graph import END, StateGraph

from .nodes.writing import (
    bootstrap_and_extract,
    run_parallel_roles,
    run_self_checks,
    run_judge,
    write_summary,
)
from .state import WritingState


def build_writing_graph() -> StateGraph:
    """Build the writing review subgraph."""
    builder = StateGraph(WritingState)

    builder.add_node("bootstrap_and_extract", bootstrap_and_extract)
    builder.add_node("run_parallel_roles", run_parallel_roles)
    builder.add_node("run_self_checks", run_self_checks)
    builder.add_node("run_judge", run_judge)
    builder.add_node("write_summary", write_summary)

    builder.set_entry_point("bootstrap_and_extract")
    builder.add_edge("bootstrap_and_extract", "run_parallel_roles")
    builder.add_edge("run_parallel_roles", "run_self_checks")
    builder.add_edge("run_self_checks", "run_judge")
    builder.add_edge("run_judge", "write_summary")
    builder.add_edge("write_summary", END)

    return builder


@functools.cache
def compile_writing_graph():
    """Compile the writing graph ready for execution (cached)."""
    return build_writing_graph().compile()
