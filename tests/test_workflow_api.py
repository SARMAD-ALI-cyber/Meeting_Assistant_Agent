"""API tests with workflow mocked (no network)."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app
from schemas import MeetingState, Task


def test_post_workflow_from_transcript_mocked(monkeypatch) -> None:
    def fake_run(transcript: str, *, run_id: str, thread_id: str) -> MeetingState:
        return MeetingState(
            transcript=transcript,
            cleaned_transcript=transcript.strip(),
            extracted_tasks=[Task(title="Mock task", confidence=0.95, owner="QA")],
            meeting_summary="Done",
        )

    monkeypatch.setattr(
        "app.api.v1.workflows.run_from_transcript",
        fake_run,
    )
    client = TestClient(app)
    res = client.post("/v1/workflows/from-transcript", json={"transcript": "  hi  "})
    assert res.status_code == 200
    body = res.json()
    assert body["cleaned_transcript"] == "hi"
    assert body["meeting_summary"] == "Done"
    assert len(body["extracted_tasks"]) == 1
    assert body["extracted_tasks"][0]["title"] == "Mock task"
    assert body["run_id"]
    assert body["thread_id"]
