"""LangGraph node: structured LLM extraction."""

from __future__ import annotations

import json
import logging
import time
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langchain_groq import ChatGroq

from app.config import get_settings
from schemas.extraction import ExtractedMeetingPayload
from schemas.state import MeetingState

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are an expert meeting analyst. Extract concrete action items from the transcript.\n\n"
    "Rules:\n"
    "- Each task must have a short actionable title and a clear description when possible.\n"
    "- Set owner to null if not explicitly stated; do not invent names.\n"
    "- Set deadline to an ISO-8601 date or datetime string only if a specific date/time is "
    "stated; otherwise null.\n"
    "- dependencies must list other task id values only when those tasks exist in your output; "
    "otherwise use empty list.\n"
    "- confidence: 0.0–1.0 for how certain you are that this is a real, assignable action item.\n"
    "- meeting_summary: optional 1–3 sentence summary of the meeting.\n"
    "- raw_decisions: optional list of non-task decisions (strings).\n"
)


def extract_node(state: MeetingState | dict[str, Any], config: RunnableConfig) -> dict[str, Any]:
    t0 = time.perf_counter()
    s = state if isinstance(state, MeetingState) else MeetingState.model_validate(state)
    run_id = (config.get("configurable") or {}).get("run_id", "unknown")

    settings = get_settings()
    text = s.cleaned_transcript or s.transcript

    if not settings.groq_api_key:
        err = "GROQ_API_KEY is not configured."
        elapsed_ms = (time.perf_counter() - t0) * 1000
        logger.info(
            json.dumps(
                {
                    "run_id": run_id,
                    "node": "extract",
                    "duration_ms": round(elapsed_ms, 2),
                    "error": err,
                }
            )
        )
        return {
            "extracted_tasks": [],
            "meeting_summary": None,
            "raw_decisions": None,
            "errors": [*s.errors, err],
        }

    llm = ChatGroq(
        model=settings.groq_model,
        temperature=0,
        max_retries=2,
        api_key=settings.groq_api_key,
    )
    structured = llm.with_structured_output(ExtractedMeetingPayload)

    try:
        payload = structured.invoke(
            [
                SystemMessage(content=SYSTEM_PROMPT),
                HumanMessage(content=f"Transcript:\n\n{text}"),
            ]
        )
        if not isinstance(payload, ExtractedMeetingPayload):
            payload = ExtractedMeetingPayload.model_validate(payload)
    except Exception as exc:  # noqa: BLE001 — surface to client
        elapsed_ms = (time.perf_counter() - t0) * 1000
        logger.exception(
            json.dumps(
                {
                    "run_id": run_id,
                    "node": "extract",
                    "duration_ms": round(elapsed_ms, 2),
                }
            )
        )
        return {
            "extracted_tasks": [],
            "meeting_summary": None,
            "raw_decisions": None,
            "errors": [*s.errors, f"extraction_failed: {exc!s}"],
        }

    elapsed_ms = (time.perf_counter() - t0) * 1000
    logger.info(
        json.dumps(
            {
                "run_id": run_id,
                "node": "extract",
                "duration_ms": round(elapsed_ms, 2),
            }
        )
    )
    return {
        "extracted_tasks": payload.tasks,
        "meeting_summary": payload.meeting_summary,
        "raw_decisions": payload.raw_decisions,
    }
