"""
Exact shape to bind to LLM structured output after the extraction node.
"""

from pydantic import BaseModel, Field

from .tasks import Task


class ExtractedMeetingPayload(BaseModel):
    tasks: list[Task] = Field(
        default_factory=list,
        description="Structured action items extracted from the transcript.",
    )
    meeting_summary: str | None = Field(
        default=None,
        description="Optional short summary of the meeting.",
    )
    raw_decisions: list[str] | None = Field(
        default=None,
        description="Optional bullet decisions as plain strings.",
    )
