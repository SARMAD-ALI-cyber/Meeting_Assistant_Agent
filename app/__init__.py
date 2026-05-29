"""FastAPI application package (avoid importing `app.main` here to prevent import cycles)."""

from .config import get_settings

__all__ = ["get_settings"]
