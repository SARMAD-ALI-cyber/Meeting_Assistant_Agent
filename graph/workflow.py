"""Build and run the Phase 1 meeting processing graph."""

from __future__ import annotations

from functools import lru_cache

from langgraph.graph import END, START, StateGraph

from graph.nodes.ambiguity import ambiguity_node
from graph.nodes.extract import extract_node
from graph.nodes.ingest import ingest_node
from schemas.state import MeetingState


@lru_cache(maxsize=1)
def get_compiled_meeting_graph():
    """Single compiled graph reused across requests (nodes read fresh Settings)."""
    builder = StateGraph(MeetingState)
    builder.add_node("ingest", ingest_node)
    builder.add_node("extract", extract_node)
    builder.add_node("ambiguity_detect", ambiguity_node)
    builder.add_edge(START, "ingest")
    builder.add_edge("ingest", "extract")
    builder.add_edge("extract", "ambiguity_detect")
    builder.add_edge("ambiguity_detect", END)
    return builder.compile()


def reset_workflow_caches() -> None:
    """Clear compiled graph cache (tests)."""
    get_compiled_meeting_graph.cache_clear()


def run_from_transcript(
    transcript: str,
    *,
    run_id: str,
    thread_id: str,
) -> MeetingState:
    """Run ingest → extract → ambiguity once and return final state."""
    graph = get_compiled_meeting_graph()
    initial = MeetingState(transcript=transcript)
    cfg: dict = {"configurable": {"run_id": run_id, "thread_id": thread_id}}
    out = graph.invoke(initial.model_dump(), config=cfg)
    return MeetingState.model_validate(out)
