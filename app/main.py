"""FastAPI entrypoint. Run: uvicorn app.main:app --reload"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1 import api_v1_router
from app.config import get_settings


@asynccontextmanager
async def lifespan(_app: FastAPI):
    s = get_settings()
    level = getattr(logging, s.log_level.upper(), logging.INFO)
    logging.basicConfig(level=level, format="%(levelname)s %(name)s %(message)s")
    yield


app = FastAPI(
    title="Meeting-to-Execution Agent",
    version="0.1.0",
    description="Phase 1: transcript → extract → ambiguity (LangGraph).",
    lifespan=lifespan,
)

app.include_router(api_v1_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health/config")
def health_config() -> dict[str, str | bool | None]:
    """Non-secret config snapshot for local debugging."""
    s = get_settings()
    return {
        "log_level": s.log_level,
        "require_approval": s.require_approval,
        "groq_model": s.groq_model,
        "groq_api_key_set": bool(s.groq_api_key),
    }
