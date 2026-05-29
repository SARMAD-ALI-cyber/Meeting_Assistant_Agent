"""API version 1 router bundle."""

from fastapi import APIRouter

from app.api.v1 import workflows

api_v1_router = APIRouter(prefix="/v1")
api_v1_router.include_router(workflows.router)
