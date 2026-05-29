"""
Single action item with stable identity for idempotency and ambiguity references.
"""

from __future__ import annotations

import uuid

from pydantic import BaseModel, Field


def _new_task_id() -> str:
    return str(uuid.uuid4())


class Task(BaseModel):
    id: str = Field(
        default_factory=_new_task_id,
        description="Stable task id for idempotency, ambiguity.task_ref, and dependencies.",
    )
    title: str = Field(
        min_length=1,
        description="Short, actionable title for the task.",
    )
    description: str = Field(
        default="",
        description="Details, acceptance criteria, or context from the meeting.",
    )
    owner: str | None = Field(
        default=None,
        description="Person or role accountable for the task, if known.",
    )
    deadline: str | None = Field(
        default=None,
        description="ISO-8601 date or datetime string when the task is due, if known.",
    )
    dependencies: list[str] = Field(
        default_factory=list,
        description=(
            "Other Task.id values this task depends on "
            "(or free-text placeholders until ids exist)."
        ),
    )
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Model confidence that this is a valid, complete action item.",
    )
