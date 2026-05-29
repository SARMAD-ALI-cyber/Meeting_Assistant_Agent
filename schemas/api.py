"""HTTP request and response bodies (no graph logic)."""

from typing import Any

from pydantic import BaseModel, Field

from .ambiguity import Ambiguity
from .tasks import Task


class TranscriptIngestRequest(BaseModel):
    transcript: str = Field(
        min_length=1,
        description="Meeting transcript or notes to process.",
    )
    metadata: dict[str, Any] | None = Field(
        default=None,
        description="Optional meeting title, external ids, source system, etc.",
    )


class WorkflowStartResponse(BaseModel):
    run_id: str = Field(description="Unique id for this workflow execution.")
    thread_id: str = Field(
        description="LangGraph thread / checkpoint key for resume and HITL."
    )
    message: str | None = Field(
        default=None,
        description="Optional human-readable status for the client.",
    )


class TranscriptWorkflowResponse(BaseModel):
    """Phase 1: result of running the ingest → extract → ambiguity graph once."""

    run_id: str = Field(description="Correlation id for this HTTP request / run.")
    thread_id: str = Field(
        description="Reserved for Phase 2 checkpointing; generated per request in Phase 1."
    )
    cleaned_transcript: str | None = Field(
        default=None,
        description="Normalized transcript after the ingest node.",
    )
    meeting_summary: str | None = Field(
        default=None,
        description="Optional summary from the extraction model.",
    )
    extracted_tasks: list[Task] = Field(default_factory=list)
    ambiguities: list[Ambiguity] = Field(default_factory=list)
    errors: list[str] = Field(
        default_factory=list,
        description="Non-fatal extraction failures or client-visible warnings.",
    )
