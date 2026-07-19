"""Unit tests for the in-memory infrastructure implementations."""

import time

from stadiummind.core.models import Incident, IncidentType, Recommendation, Severity
from stadiummind.infra.bus import InMemoryBus
from stadiummind.infra.cache import InMemoryStore
from stadiummind.infra.repository import InMemoryRepository


def test_bus_delivers_to_subscribers():
    bus = InMemoryBus()
    received = []
    bus.subscribe("t", received.append)
    bus.publish("t", {"x": 1})
    assert received == [{"x": 1}]


def test_bus_isolates_failing_subscriber():
    bus = InMemoryBus()
    good = []

    def bad(_msg):
        raise RuntimeError("boom")

    bus.subscribe("t", bad)
    bus.subscribe("t", good.append)
    bus.publish("t", {"ok": True})  # must not raise
    assert good == [{"ok": True}]


def test_cache_set_get_delete():
    store = InMemoryStore()
    store.set("k", {"v": 1})
    assert store.get("k") == {"v": 1}
    store.delete("k")
    assert store.get("k") is None


def test_cache_ttl_expiry():
    store = InMemoryStore()
    store.set("k", 1, ttl_seconds=0.01)
    time.sleep(0.02)
    assert store.get("k") is None


def test_repository_incident_lifecycle():
    repo = InMemoryRepository()
    inc = repo.save_incident(
        Incident.create(IncidentType.MEDICAL, Severity.HIGH, "med_1", "x")
    )
    assert len(repo.list_incidents(include_resolved=False)) == 1
    repo.resolve_incident(inc.id)
    assert repo.list_incidents(include_resolved=False) == []
    assert len(repo.list_incidents(include_resolved=True)) == 1


def test_repository_recommendation_decision():
    repo = InMemoryRepository()
    rec = repo.save_recommendation(
        Recommendation.create("crowd", "t", "e", 0.9)
    )
    updated = repo.set_recommendation_decision(rec.id, True)
    assert updated.approved is True
    assert repo.set_recommendation_decision("missing", True) is None
