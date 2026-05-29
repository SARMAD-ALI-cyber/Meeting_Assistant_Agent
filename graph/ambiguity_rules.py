"""Rule-based ambiguity detection (no LLM)."""

from __future__ import annotations

from schemas import Ambiguity, AmbiguityKind, Task


def collect_ambiguities(tasks: list[Task], *, confidence_threshold: float) -> list[Ambiguity]:
    """Return new ambiguity records for the given extracted tasks."""
    out: list[Ambiguity] = []
    id_set = {t.id for t in tasks}

    for task in tasks:
        owner = (task.owner or "").strip()
        if not owner:
            out.append(
                Ambiguity(
                    task_ref=task.id,
                    kind=AmbiguityKind.MISSING_OWNER,
                    message="Task has no accountable owner.",
                )
            )

        deadline = (task.deadline or "").strip()
        if not deadline:
            out.append(
                Ambiguity(
                    task_ref=task.id,
                    kind=AmbiguityKind.MISSING_DEADLINE,
                    message="Task has no deadline or due date.",
                )
            )

        if task.confidence < confidence_threshold:
            out.append(
                Ambiguity(
                    task_ref=task.id,
                    kind=AmbiguityKind.LOW_CONFIDENCE,
                    message=(
                        f"Confidence {task.confidence:.2f} is below threshold "
                        f"{confidence_threshold:.2f}."
                    ),
                )
            )

        for dep in task.dependencies:
            d = dep.strip()
            if not d:
                continue
            if d not in id_set:
                out.append(
                    Ambiguity(
                        task_ref=task.id,
                        kind=AmbiguityKind.UNCLEAR_DEPENDENCY,
                        message=f"Dependency {d!r} does not match any extracted task id.",
                    )
                )

    return out
