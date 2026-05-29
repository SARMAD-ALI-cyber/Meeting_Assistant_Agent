"""Consistent error payload for FastAPI exception handlers."""

from pydantic import BaseModel, Field


class ApiError(BaseModel):
    detail: str = Field(description="Primary error message.")
    code: str | None = Field(default=None, description="Stable machine-readable error code.")
    field_errors: dict[str, list[str]] | None = Field(
        default=None,
        description="Per-field validation or domain errors.",
    )
