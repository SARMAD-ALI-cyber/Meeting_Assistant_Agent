"""One human- or rule-detected issue tied to extraction or HITL."""

from pydantic import BaseModel, Field

from .enums import AmbiguityKind


class Ambiguity(BaseModel):
    task_ref: str | None = Field(
        default=None,
        description="Task.id when the ambiguity applies to a specific extracted task.",
    )
    kind: AmbiguityKind = Field(description="Category of ambiguity for routing and UX.")
    message: str = Field(
        min_length=1,
        description="User-facing explanation for Slack, UI, or logs.",
    )
