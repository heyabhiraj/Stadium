"""End-to-end system test of the 7-step hackathon demo narrative.

This single test walks the exact story from implementation.md and asserts the
system behaves correctly at each beat. It is the highest-level guarantee that
all layers - simulation, ML, optimisation, agents and API - work together.

    1. Fan enters the stadium.
    2. AI routes them to the least crowded gate.
    3. Crowd congestion is predicted at Gate 3.
    4. The operator receives a redirect recommendation with an explanation.
    5. A medical incident occurs; a volunteer is dispatched.
    6. Nearby fans are rerouted.
    7. After the match, AI recommends the best exit/transport.
"""


def _auth(client, role="operations"):
    token = client.post(
        "/api/auth/login", json={"username": "op", "role": role}
    ).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_full_demo_story(client):
    service = client._service

    # -- Step 1: fan enters -------------------------------------------------
    heat = client.get("/api/crowd/heatmap").json()
    gates = {z["id"]: z for z in heat if z["type"] == "gate"}
    assert len(gates) == 4

    # -- Step 2: route the fan to the least-crowded gate --------------------
    least_gate = min(gates.values(), key=lambda z: z["ratio"])["id"]
    route = client.post(
        "/api/ai/query",
        json={
            "intent": "navigate",
            "params": {"origin": least_gate, "destination": "stand_n"},
        },
    ).json()
    assert route["metadata"]["path"][0] == least_gate

    # -- Step 3: congestion builds at Gate 3 --------------------------------
    client.post("/api/crowd/surge", params={"zone_id": "gate_3", "people": 8000})
    for _ in range(4):
        client.post("/api/crowd/tick")
    heat = {z["id"]: z for z in client.get("/api/crowd/heatmap").json()}
    # Gate 3 must now be busier than every *other* gate.
    other_gate_ratios = [
        z["ratio"] for zid, z in heat.items()
        if z["type"] == "gate" and zid != "gate_3"
    ]
    assert heat["gate_3"]["ratio"] > max(other_gate_ratios)

    # -- Step 4: operator receives an explained redirect recommendation -----
    recs = client.get("/api/ai/recommendations").json()
    crowd_recs = [r for r in recs if r["agent"] == "crowd"]
    assert crowd_recs, "crowd agent should raise a recommendation"
    redirect = crowd_recs[0]
    assert redirect["explanation"]           # explain-before-recommend
    assert redirect["actions"]               # actionable
    assert redirect["metadata"]["alternative"] != "gate_3"

    # Operator approves it (human-in-the-loop).
    approved = client.post(
        f"/api/ai/recommendations/{redirect['id']}/decision",
        headers=_auth(client),
        json={"approved": True},
    ).json()
    assert approved["approved"] is True

    # -- Step 5: a medical incident triggers volunteer dispatch -------------
    client.post(
        "/api/incidents",
        headers=_auth(client, "medical"),
        json={
            "type": "medical",
            "severity": "critical",
            "zone_id": "med_1",
            "description": "fan collapsed in west concourse",
        },
    )
    recs = client.get("/api/ai/recommendations").json()
    dispatch = [r for r in recs if r["agent"] == "emergency" and "Dispatch" in r["title"]]
    assert dispatch, "emergency agent should dispatch volunteers"
    assert dispatch[0]["metadata"]["volunteers"] >= 1

    # -- Step 6: nearby fans are rerouted -----------------------------------
    reroute = [r for r in recs if r["agent"] == "emergency" and "Reroute" in r["title"]]
    assert reroute, "emergency agent should reroute nearby fans"

    # -- Step 7: after full time, best exit/transport is recommended --------
    # Fast-forward the match clock past full time.
    service.match_minute = 90
    egress = client.post(
        "/api/ai/query",
        json={"intent": "best_exit", "params": {}},
    ).json()
    assert egress["agent"] == "transport"
    assert egress["metadata"]["option"] in {"metro", "parking"}
