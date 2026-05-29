"""Phase 0: schemas package imports and JSON-safe serialization."""

import json

from schemas import (
    Ambiguity,
    AmbiguityKind,
    ApiError,
    ExtractedMeetingPayload,
    MeetingState,
    Task,
    TranscriptIngestRequest,
    WorkflowStartResponse,
)


def test_task_defaults_and_json() -> None:
    t = Task(title="Ship report", confidence=0.9)
    assert t.id
    data = t.model_dump(mode="json")
    json.dumps(data)


def test_meeting_state_round_trip() -> None:
    s = MeetingState(
        transcript="Discussed Q1.",
        extracted_tasks=[
            Task(title="A", confidence=1.0),
        ],
    )
    payload = json.loads(s.model_dump_json())
    s2 = MeetingState.model_validate(payload)
    assert s2.transcript == "Discussed Q1."
    assert len(s2.extracted_tasks) == 1


def test_api_models() -> None:
    req = TranscriptIngestRequest(transcript="Hello")
    assert req.model_dump(mode="json")["transcript"] == "Hello"
    resp = WorkflowStartResponse(run_id="r1", thread_id="t1")
    json.dumps(resp.model_dump(mode="json"))


def test_extraction_and_ambiguity() -> None:
    p = ExtractedMeetingPayload(
        tasks=[Task(title="x", confidence=0.5)],
        meeting_summary="m",
    )
    json.dumps(p.model_dump(mode="json"))
    a = Ambiguity(
        task_ref=None,
        kind=AmbiguityKind.OTHER,
        message="unclear",
    )
    assert a.kind == AmbiguityKind.OTHER


def test_api_error() -> None:
    e = ApiError(detail="bad", code="VALIDATION")
    json.dumps(e.model_dump(mode="json"))


def test_graph_imports_schemas_without_cycles() -> None:
    from graph import __doc__ as gd  # noqa: PLC0415

    assert gd
