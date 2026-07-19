"""Unit tests for core domain models."""

from stadiummind.core.models import (
    Alert,
    CongestionLevel,
    CrowdReading,
    Incident,
    IncidentType,
    Recommendation,
    Severity,
    occupancy_ratio,
)


def test_occupancy_ratio_handles_zero_capacity():
    assert occupancy_ratio(10, 0) == 0.0
    assert occupancy_ratio(50, 100) == 0.5


def test_congestion_level_buckets():
    assert CongestionLevel.from_ratio(0.10) is CongestionLevel.NORMAL
    assert CongestionLevel.from_ratio(0.60) is CongestionLevel.MODERATE
    assert CongestionLevel.from_ratio(0.80) is CongestionLevel.BUSY
    assert CongestionLevel.from_ratio(0.95) is CongestionLevel.CONGESTED


def test_crowd_reading_ratio_and_level():
    r = CrowdReading(zone_id="g", occupancy=90, capacity=100, arrival_rate_per_min=5)
    assert r.ratio == 0.9
    assert r.level is CongestionLevel.CONGESTED


def test_recommendation_clamps_confidence():
    rec = Recommendation.create("crowd", "t", "e", confidence=1.5)
    assert rec.confidence == 1.0
    assert rec.approved is None
    assert rec.id.startswith("rec_")


def test_incident_factory():
    inc = Incident.create(IncidentType.MEDICAL, Severity.HIGH, "med_1", "collapse")
    assert inc.id.startswith("inc_")
    assert not inc.resolved
    assert inc.severity is Severity.HIGH


def test_alert_factory():
    a = Alert.create("busy", CongestionLevel.BUSY, "gate_1")
    assert a.level is CongestionLevel.BUSY
    assert a.zone_id == "gate_1"
