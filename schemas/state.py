"""Workflow / graph state aligned with CLAUDE.md MeetingState."""

from typing import Any

from pydantic import BaseModel, Field

from .ambiguity import Ambiguity
from .enums import ApprovalStatus
from .tasks import Task


class MeetingState(BaseModel):
    transcript: str = Field(default="", description="Raw meeting transcript input.")
    cleaned_transcript: str | None = Field(
        default=None,
        description="Normalized transcript after ingestion.",
    )
    extracted_tasks: list[Task] = Field(default_factory=list)
    ambiguities: list[Ambiguity] = Field(default_factory=list)
    clarified_tasks: list[Task] = Field(
        default_factory=list,
        description="Tasks after human clarification; merge policy defined in Phase 2+.",
    )
    approval_status: ApprovalStatus = Field(default=ApprovalStatus.PENDING)
    created_task_ids: list[str] = Field(
        default_factory=list,
        description="Ids returned from external systems (Jira, Notion, etc.).",
    )
    followup_schedule: dict[str, Any] = Field(
        default_factory=dict,
        description="Scheduler metadata; structure refined when follow-up automation lands.",
    )
    memory_refs: list[str] = Field(
        default_factory=list,
        description="References into vector or structured long-term memory.",
    )
    errors: list[str] = Field(
        default_factory=list,
        description="Append-only node or tool errors for observability and recovery.",
    )
    meeting_summary: str | None = Field(
        default=None,
        description="Filled by extraction node; surfaced on API responses.",
    )
    raw_decisions: list[str] | None = Field(
        default=None,
        description="Optional bullet decisions from extraction.",
    )
