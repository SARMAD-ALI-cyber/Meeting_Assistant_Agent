"""Pytest fixtures."""

from __future__ import annotations

import pytest

from graph.workflow import reset_workflow_caches


@pytest.fixture(autouse=True)
def _reset_workflow_cache() -> None:
    reset_workflow_caches()
    yield
    reset_workflow_caches()
