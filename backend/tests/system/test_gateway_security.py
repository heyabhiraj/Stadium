"""System tests for gateway security controls: headers, CORS, rate limit, validation."""

import pytest
from fastapi.testclient import TestClient

from stadiummind.api.app import create_app
from stadiummind.api.service import StadiumService
from stadiummind.core.config import Settings


def _client(**overrides):
    settings = Settings(force_mock_llm=True, **overrides)
    return TestClient(create_app(StadiumService(settings)))


def test_security_headers_present():
    c = _client()
    r = c.get("/api/health")
    assert r.headers["x-content-type-options"] == "nosniff"
    assert r.headers["x-frame-options"] == "DENY"
    assert "default-src 'none'" in r.headers["content-security-policy"]
    assert r.headers["cache-control"] == "no-store"
    # HSTS only in production.
    assert "strict-transport-security" not in r.headers


def test_hsts_in_production():
    c = _client(
        environment="production",
        jwt_secret="strong",
        allowed_origins=("https://app.example",),
    )
    r = c.get("/api/health")
    assert "strict-transport-security" in r.headers


def test_cors_allows_configured_origin_only():
    c = _client(allowed_origins=("http://localhost:3000",))
    ok = c.get("/api/health", headers={"Origin": "http://localhost:3000"})
    assert ok.headers.get("access-control-allow-origin") == "http://localhost:3000"
    evil = c.get("/api/health", headers={"Origin": "http://evil.example"})
    assert evil.headers.get("access-control-allow-origin") != "http://evil.example"


def test_rate_limit_returns_429_and_exempts_health():
    c = _client(rate_limit_per_minute=3)
    # Health is exempt: many calls stay 200.
    for _ in range(5):
        assert c.get("/api/health").status_code == 200
    # Non-exempt endpoint: 4th call within the window is throttled.
    codes = [c.get("/api/venue").status_code for _ in range(4)]
    assert codes[:3] == [200, 200, 200]
    assert codes[3] == 429


def test_login_rejects_invalid_username():
    c = _client()
    bad = c.post("/api/auth/login", json={"username": "<script>", "role": "fan"})
    assert bad.status_code == 422


def test_query_rejects_malformed_intent():
    c = _client()
    bad = c.post("/api/ai/query", json={"intent": "Nav-IGATE!", "params": {}})
    assert bad.status_code == 422


def test_incident_description_length_enforced():
    c = _client()
    token = c.post("/api/auth/login", json={"username": "op", "role": "operations"}).json()["access_token"]
    bad = c.post(
        "/api/incidents",
        headers={"Authorization": f"Bearer {token}"},
        json={"type": "medical", "severity": "high", "zone_id": "med_1", "description": "x" * 600},
    )
    assert bad.status_code == 422


def test_surge_upper_bound_enforced():
    c = _client(max_surge_people=1000)
    r = c.post("/api/crowd/surge", params={"zone_id": "gate_1", "people": 5000})
    assert r.status_code == 400


def test_unsafe_production_app_refuses_to_start():
    # Default secret + production => create_app must raise via the guard.
    from stadiummind.core.exceptions import ConfigurationError

    settings = Settings(force_mock_llm=True, environment="production")
    with pytest.raises(ConfigurationError):
        create_app(StadiumService(settings))
