"""API v1 routes."""

from __future__ import annotations

import uuid

from fastapi import APIRouter

from graph.workflow import run_from_transcript
from schemas import TranscriptIngestRequest, TranscriptWorkflowResponse

router = APIRouter(tags=["workflows"])


@router.post(
    "/workflows/from-transcript",
    response_model=TranscriptWorkflowResponse,
    summary="Run Phase 1 graph on a transcript",
)
def post_workflow_from_transcript(body: TranscriptIngestRequest) -> TranscriptWorkflowResponse:
    """Ingest → extract (Groq) → ambiguity rules."""
    run_id = str(uuid.uuid4())
    thread_id = str(uuid.uuid4())
    final = run_from_transcript(body.transcript, run_id=run_id, thread_id=thread_id)
    return TranscriptWorkflowResponse(
        run_id=run_id,
        thread_id=thread_id,
        cleaned_transcript=final.cleaned_transcript,
        meeting_summary=final.meeting_summary,
        extracted_tasks=final.extracted_tasks,
        ambiguities=final.ambiguities,
        errors=final.errors,
    )
