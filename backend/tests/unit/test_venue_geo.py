"""Unit tests for the venue geo-projection."""

import pytest

from stadiummind.core.venue import METLIFE, build_default_venue


def test_all_zones_are_geolocated(venue):
    for zone in venue:
        assert zone.lat is not None and zone.lng is not None


def test_projection_is_near_anchor(venue):
    # A zone near the centre should be within a few hundred metres of MetLife.
    conc = venue.get("conc_n")
    assert abs(conc.lat - METLIFE.lat) < 0.01
    assert abs(conc.lng - METLIFE.lng) < 0.01


def test_north_is_higher_latitude(venue):
    # gate_1 (y=0.15, north) must have a higher latitude than gate_5 (y=0.85).
    assert venue.get("gate_1").lat > venue.get("gate_5").lat


def test_east_is_greater_longitude(venue):
    # gate_3 (x=0.90, east) must have a greater longitude than gate_1 (x=0.10).
    assert venue.get("gate_3").lng > venue.get("gate_1").lng


def test_landmark_overrides_preserved():
    v = build_default_venue()
    # Metro was pinned to the real Meadowlands station, not the projected grid.
    assert v.get("metro").lat == pytest.approx(40.814890)
    assert v.get("metro").lng == pytest.approx(-74.077260)


def test_distance_uses_footprint(venue):
    # Two zones one full grid-width apart are ~footprint metres apart.
    d = venue.distance("gate_1", "gate_3")  # dx = 0.8 in x
    assert 200 < d < venue.anchor.footprint_m + 50
