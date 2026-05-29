"""LangGraph node: normalize transcript."""

from __future__ import annotations

import json
import logging
import time
from typing import Any

from langchain_core.runnables import RunnableConfig

from app.config import get_settings
from graph.ingest_utils import normalize_transcript
from schemas.state import MeetingState

logger = logging.getLogger(__name__)


def ingest_node(state: MeetingState | dict[str, Any], config: RunnableConfig) -> dict[str, Any]:
    t0 = time.perf_counter()
    s = state if isinstance(state, MeetingState) else MeetingState.model_validate(state)
    run_id = (config.get("configurable") or {}).get("run_id", "unknown")

    settings = get_settings()
    cleaned, truncated = normalize_transcript(
        s.transcript,
        max_chars=settings.transcript_max_chars,
    )
    if truncated:
        msg = (
            f"Transcript truncated to {settings.transcript_max_chars} characters "
            "after normalization."
        )
        logger.warning(json.dumps({"run_id": run_id, "node": "ingest", "warning": msg}))

    elapsed_ms = (time.perf_counter() - t0) * 1000
    logger.info(
        json.dumps(
            {
                "run_id": run_id,
                "node": "ingest",
                "duration_ms": round(elapsed_ms, 2),
            }
        )
    )
    return {"cleaned_transcript": cleaned}
