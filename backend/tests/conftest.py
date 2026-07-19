"""Shared pytest fixtures.

The mock LLM is forced on for the whole test session so every test is
deterministic, offline and free. Real Gemini is exercised separately (and
manually) via a live API key.
"""

from __future__ import annotations

import os

import pytest

# Force deterministic, offline behaviour BEFORE any settings are read.
os.environ["FORCE_MOCK_LLM"] = "1"
os.environ.setdefault("SIMULATION_SEED", "42")

from stadiummind.core.config import get_settings  # noqa: E402
from stadiummind.core.venue import build_default_venue  # noqa: E402


@pytest.fixture(autouse=True)
def _clear_settings_cache():
    """Ensure each test sees settings built from the current environment."""
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def settings():
    return get_settings()


@pytest.fixture
def venue():
    return build_default_venue()


@pytest.fixture
def service():
    """A fresh, warmed-up StadiumService using in-memory infra + mock LLM."""
    from stadiummind.api.service import StadiumService

    return StadiumService(get_settings())


@pytest.fixture
def client(service):
    """A FastAPI TestClient wrapping a shared service instance."""
    from fastapi.testclient import TestClient

    from stadiummind.api.app import create_app

    app = create_app(service)
    with TestClient(app) as test_client:
        test_client._service = service  # convenience handle for assertions
        yield test_client
