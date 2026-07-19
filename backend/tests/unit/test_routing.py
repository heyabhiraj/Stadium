"""Unit tests for the routing engine."""

import pytest

from stadiummind.core.models import CrowdReading
from stadiummind.optimization.routing import RouteOptimizer


def _reading(zone_id, ratio, capacity=1000):
    return CrowdReading(
        zone_id=zone_id,
        occupancy=int(ratio * capacity),
        capacity=capacity,
        arrival_rate_per_min=1.0,
    )


def test_route_connects_origin_and_destination(venue):
    r = RouteOptimizer(venue).route("gate_1", "stand_s")
    assert r.path[0] == "gate_1"
    assert r.path[-1] == "stand_s"
    assert r.distance_m > 0
    assert r.eta_minutes > 0


def test_same_origin_destination_is_trivial(venue):
    r = RouteOptimizer(venue).route("gate_1", "gate_1")
    assert r.path == ["gate_1"]
    assert r.distance_m == 0


def test_avoid_congestion_reroutes_around_hotspot(venue):
    """When a cheaper path runs through a congested zone and an alternative
    exists, the congestion-aware route must actually avoid the hotspot."""
    opt = RouteOptimizer(venue)

    # By pure distance, gate_1 -> stand_s goes through the West Concourse.
    crowd_calm = {z.id: _reading(z.id, 0.0) for z in venue}
    plain = opt.route("gate_1", "stand_s", crowd=crowd_calm, avoid_congestion=False)
    assert "conc_w" in plain.path, "baseline shortest path should use conc_w"

    # Now congest the West Concourse; the avoiding route must detour around it.
    crowd_hot = dict(crowd_calm)
    crowd_hot["conc_w"] = _reading("conc_w", 1.0)
    avoiding = opt.route("gate_1", "stand_s", crowd=crowd_hot, avoid_congestion=True)
    assert "conc_w" not in avoiding.path, "avoiding route must skip the hotspot"
    assert avoiding.path[0] == "gate_1" and avoiding.path[-1] == "stand_s"


def test_avoid_flag_is_reported(venue):
    opt = RouteOptimizer(venue)
    crowd = {z.id: _reading(z.id, 0.0) for z in venue}
    assert opt.route("gate_1", "stand_n", crowd=crowd, avoid_congestion=True).avoids_congestion
    assert not opt.route("gate_1", "stand_n", crowd=crowd).avoids_congestion


def test_unknown_zone_raises(venue):
    with pytest.raises(KeyError):
        RouteOptimizer(venue).route("nope", "gate_1")
