"""Unit tests for individual agents and the orchestrator."""

from stadiummind.agents.accessibility_agent import AccessibilityAgent
from stadiummind.agents.crowd_agent import CrowdAgent
from stadiummind.agents.emergency_agent import EmergencyAgent
from stadiummind.agents.navigation_agent import NavigationAgent
from stadiummind.agents.orchestrator import AIOrchestrator
from stadiummind.core.models import (
    CrowdReading,
    Incident,
    IncidentType,
    Severity,
)
from stadiummind.core.venue import build_default_venue


def _crowd(venue, ratios=None, arrivals=None):
    """Build a crowd snapshot with optional per-zone ratio / arrival overrides."""
    ratios = ratios or {}
    arrivals = arrivals or {}
    snap = {}
    for z in venue:
        ratio = ratios.get(z.id, 0.1)
        snap[z.id] = CrowdReading(
            zone_id=z.id,
            occupancy=int(ratio * z.capacity),
            capacity=z.capacity,
            arrival_rate_per_min=arrivals.get(z.id, 2.0),
        )
    return snap


def _orch(venue):
    return AIOrchestrator(venue)


def test_crowd_agent_recommends_redirect_when_gate_congested(venue):
    orch = _orch(venue)
    crowd = _crowd(
        venue,
        ratios={"gate_3": 0.95, "gate_5": 0.05},
        arrivals={"gate_3": 120.0},  # far exceeds turnstile capacity
    )
    ctx = orch.build_context(crowd, match_minute=40)
    recs = CrowdAgent().analyze(ctx)
    assert recs, "expected a redirect recommendation for a congested gate"
    top = recs[0]
    assert "gate_3" == top.zone_id
    assert top.metadata["alternative"] == "gate_5"
    assert top.confidence > 0.5


def test_crowd_agent_quiet_when_calm(venue):
    orch = _orch(venue)
    crowd = _crowd(venue, ratios={g.id: 0.1 for g in venue}, arrivals={})
    ctx = orch.build_context(crowd, match_minute=20)
    assert CrowdAgent().analyze(ctx) == []


def test_navigation_agent_reactive_route(venue):
    orch = _orch(venue)
    ctx = orch.build_context(
        _crowd(venue), match_minute=10,
        query={"origin": "gate_1", "destination": "stand_s"},
    )
    rec = NavigationAgent().handle_query(ctx)
    assert rec is not None
    assert rec.metadata["path"][0] == "gate_1"
    assert rec.metadata["path"][-1] == "stand_s"


def test_navigation_agent_requires_params(venue):
    orch = _orch(venue)
    ctx = orch.build_context(_crowd(venue), match_minute=10, query={})
    assert NavigationAgent().handle_query(ctx) is None


def test_emergency_agent_dispatches_on_incident(venue):
    orch = _orch(venue)
    incident = Incident.create(
        IncidentType.MEDICAL, Severity.CRITICAL, "med_1", "fan collapsed"
    )
    ctx = orch.build_context(
        _crowd(venue), match_minute=55, incidents=[incident]
    )
    recs = EmergencyAgent().analyze(ctx)
    titles = [r.title for r in recs]
    assert any("Dispatch" in t for t in titles)
    dispatch = next(r for r in recs if "Dispatch" in r.title)
    assert dispatch.metadata["volunteers"] >= 1


def test_accessibility_agent_step_free_route(venue):
    orch = _orch(venue)
    ctx = orch.build_context(
        _crowd(venue), match_minute=10,
        query={"origin": "gate_1", "destination": "med_1"},
    )
    rec = AccessibilityAgent().handle_query(ctx)
    assert rec is not None
    assert rec.metadata["accessible"] is True


def test_orchestrator_ranks_by_severity(venue):
    orch = _orch(venue)
    crowd = _crowd(
        venue, ratios={"gate_3": 0.95}, arrivals={"gate_3": 120.0}
    )
    incident = Incident.create(
        IncidentType.MEDICAL, Severity.CRITICAL, "med_1", "collapse"
    )
    recs = orch.analyze(crowd, match_minute=60, incidents=[incident])
    assert recs
    # The critical incident recommendation should outrank routine ones.
    assert recs[0].severity in (Severity.CRITICAL, Severity.HIGH)


def test_orchestrator_supported_intents(venue):
    intents = _orch(venue).supported_intents()
    assert "navigate" in intents
    assert "best_exit" in intents


def test_orchestrator_survives_failing_agent(venue):
    """A raising agent must not break the whole analysis cycle."""

    class BoomAgent(CrowdAgent):
        name = "boom"

        def analyze(self, context):
            raise RuntimeError("kaboom")

    orch = AIOrchestrator(venue, agents=[BoomAgent(), NavigationAgent()])
    # Should return without raising even though BoomAgent explodes.
    assert orch.analyze(_crowd(venue), match_minute=10) == []
