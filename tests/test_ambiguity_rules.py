"""Unit tests for `graph.ambiguity_rules`."""

from graph.ambiguity_rules import collect_ambiguities
from schemas import AmbiguityKind, Task


def test_missing_owner_and_deadline_and_low_confidence() -> None:
    t = Task(title="Do thing", confidence=0.2, owner=None, deadline=None)
    amb = collect_ambiguities([t], confidence_threshold=0.6)
    kinds = {a.kind for a in amb}
    assert AmbiguityKind.MISSING_OWNER in kinds
    assert AmbiguityKind.MISSING_DEADLINE in kinds
    assert AmbiguityKind.LOW_CONFIDENCE in kinds


def test_unclear_dependency() -> None:
    a = Task(title="A", confidence=1.0, owner="x", deadline="2026-01-01")
    b = Task(
        title="B",
        confidence=1.0,
        owner="x",
        deadline="2026-01-02",
        dependencies=["not-an-id"],
    )
    amb = collect_ambiguities([a, b], confidence_threshold=0.6)
    assert any(x.kind == AmbiguityKind.UNCLEAR_DEPENDENCY for x in amb)
