"""LangGraph node: deterministic ambiguity detection."""

from __future__ import annotations

import json
import logging
import time
from typing import Any

from langchain_core.runnables import RunnableConfig

from app.config import get_settings
from graph.ambiguity_rules import collect_ambiguities
from schemas.state import MeetingState

logger = logging.getLogger(__name__)


def ambiguity_node(state: MeetingState | dict[str, Any], config: RunnableConfig) -> dict[str, Any]:
    t0 = time.perf_counter()
    s = state if isinstance(state, MeetingState) else MeetingState.model_validate(state)
    run_id = (config.get("configurable") or {}).get("run_id", "unknown")

    settings = get_settings()
    ambiguities = collect_ambiguities(
        s.extracted_tasks,
        confidence_threshold=settings.extraction_confidence_threshold,
    )

    elapsed_ms = (time.perf_counter() - t0) * 1000
    logger.info(
        json.dumps(
            {
                "run_id": run_id,
                "node": "ambiguity_detect",
                "duration_ms": round(elapsed_ms, 2),
            }
        )
    )
    return {"ambiguities": ambiguities}
