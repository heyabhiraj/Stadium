"""System tests exercising the HTTP API via FastAPI's TestClient."""


def _token(client, role):
    resp = client.post("/api/auth/login", json={"username": "u", "role": role})
    assert resp.status_code == 200
    return resp.json()["access_token"]


def test_health(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["llm"] == "mock"  # forced in tests


def test_venue_and_heatmap(client):
    venue = client.get("/api/venue").json()
    assert len(venue["zones"]) == 19
    assert venue["anchor"]["name"] == "MetLife Stadium"
    assert all(z["lat"] is not None and z["lng"] is not None for z in venue["zones"])
    heat = client.get("/api/crowd/heatmap").json()
    assert len(heat) == 19
    assert {"id", "level", "ratio", "x", "y", "lat", "lng"} <= set(heat[0])


def test_match_endpoint(client):
    body = client.get("/api/match").json()
    assert body["home_team"] == "Brazil"
    assert body["venue"] == "MetLife Stadium"
    assert body["source"] == "mock"  # no football-data key in tests


def test_health_reports_integrations(client):
    body = client.get("/api/health").json()
    assert body["match_source"] == "mock"
    assert body["directions_provider"] == "haversine"
    assert body["maps_enabled"] is False
    assert body["venue"] == "MetLife Stadium"


def test_directions_between_zones(client):
    body = client.get("/api/directions", params={"origin": "gate_1", "destination": "metro"}).json()
    assert body["provider"] == "haversine"       # no Google key in tests
    assert body["distance_m"] > 0
    assert len(body["polyline"]) >= 2
    assert body["polyline"][0][0] is not None


def test_directions_unknown_zone_404(client):
    resp = client.get("/api/directions", params={"origin": "nope", "destination": "metro"})
    assert resp.status_code == 404


def test_tick_advances_minute(client):
    before = client.get("/api/health").json()["match_minute"]
    client.post("/api/crowd/tick")
    after = client.get("/api/health").json()["match_minute"]
    assert after == before + 1


def test_ai_query_navigation(client):
    resp = client.post(
        "/api/ai/query",
        json={
            "intent": "navigate",
            "params": {"origin": "gate_1", "destination": "stand_s"},
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["metadata"]["path"][0] == "gate_1"


def test_ai_query_unknown_intent_404(client):
    resp = client.post("/api/ai/query", json={"intent": "teleport", "params": {}})
    assert resp.status_code == 404


def test_incident_requires_auth(client):
    resp = client.post(
        "/api/incidents",
        json={
            "type": "medical",
            "severity": "high",
            "zone_id": "med_1",
            "description": "x",
        },
    )
    assert resp.status_code == 401


def test_incident_flow_with_auth(client):
    token = _token(client, "operations")
    headers = {"Authorization": f"Bearer {token}"}
    created = client.post(
        "/api/incidents",
        headers=headers,
        json={
            "type": "medical",
            "severity": "critical",
            "zone_id": "med_1",
            "description": "fan collapsed",
        },
    )
    assert created.status_code == 200
    inc_id = created.json()["id"]

    listing = client.get("/api/incidents?include_resolved=false").json()
    assert any(i["id"] == inc_id for i in listing)

    resolved = client.post(f"/api/incidents/{inc_id}/resolve", headers=headers)
    assert resolved.status_code == 200
    assert resolved.json()["resolved"] is True


def test_fan_role_cannot_report_incident(client):
    token = _token(client, "fan")
    resp = client.post(
        "/api/incidents",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "type": "security",
            "severity": "low",
            "zone_id": "gate_1",
            "description": "x",
        },
    )
    assert resp.status_code == 403


def test_recommendation_decision_roundtrip(client):
    # Force a congestion surge so at least one recommendation exists.
    client.post("/api/crowd/surge", params={"zone_id": "gate_3", "people": 6000})
    for _ in range(3):
        client.post("/api/crowd/tick")
    recs = client.get("/api/ai/recommendations").json()
    assert recs, "expected recommendations after a surge"

    token = _token(client, "operations")
    rec_id = recs[0]["id"]
    decision = client.post(
        f"/api/ai/recommendations/{rec_id}/decision",
        headers={"Authorization": f"Bearer {token}"},
        json={"approved": True},
    )
    assert decision.status_code == 200
    assert decision.json()["approved"] is True


def test_surge_unknown_zone_404(client):
    resp = client.post("/api/crowd/surge", params={"zone_id": "nope", "people": 10})
    assert resp.status_code == 404


def test_recommendations_are_idempotent_and_preserve_decisions(client):
    # Create a stable congestion situation.
    client.post("/api/crowd/surge", params={"zone_id": "gate_3", "people": 8000})
    for _ in range(2):
        client.post("/api/crowd/tick")

    first = client.get("/api/ai/recommendations").json()
    assert first
    ids_first = {r["id"] for r in first}

    # Re-analysing the same situation must not create duplicate ids.
    second = client.get("/api/ai/recommendations").json()
    assert {r["id"] for r in second} == ids_first

    # Approve one, then re-poll: the decision must survive.
    token = _token(client, "operations")
    rec_id = first[0]["id"]
    client.post(
        f"/api/ai/recommendations/{rec_id}/decision",
        headers={"Authorization": f"Bearer {token}"},
        json={"approved": True},
    )
    third = client.get("/api/ai/recommendations").json()
    approved = next((r for r in third if r["id"] == rec_id), None)
    assert approved is not None and approved["approved"] is True


def test_negative_surge_rejected(client):
    resp = client.post("/api/crowd/surge", params={"zone_id": "gate_1", "people": -5})
    assert resp.status_code == 400
