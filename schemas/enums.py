"""Shared string enums for API, graph, and persistence."""

from enum import StrEnum


class AmbiguityKind(StrEnum):
    MISSING_OWNER = "missing_owner"
    MISSING_DEADLINE = "missing_deadline"
    LOW_CONFIDENCE = "low_confidence"
    UNCLEAR_DEPENDENCY = "unclear_dependency"
    OTHER = "other"


class ApprovalStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    SKIPPED = "skipped"
