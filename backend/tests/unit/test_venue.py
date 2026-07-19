"""Unit tests for the venue graph."""

import pytest

from stadiummind.core.models import ZoneType
from stadiummind.core.venue import build_default_venue


def test_default_venue_has_expected_zones(venue):
    assert len(venue) == 19
    assert len(venue.of_type(ZoneType.GATE)) == 4
    assert "gate_1" in venue and "metro" in venue


def test_graph_is_undirected(venue):
    # gate_1 connects to conc_n, so conc_n must connect back.
    assert "conc_n" in venue.get("gate_1").neighbours
    assert "gate_1" in venue.get("conc_n").neighbours


def test_distance_is_symmetric_and_positive(venue):
    d1 = venue.distance("gate_1", "gate_7")
    d2 = venue.distance("gate_7", "gate_1")
    assert d1 == pytest.approx(d2)
    assert d1 > 0
    assert venue.distance("gate_1", "gate_1") == 0.0


def test_connect_unknown_zone_raises():
    v = build_default_venue()
    with pytest.raises(KeyError):
        v.connect("gate_1", "does_not_exist")
