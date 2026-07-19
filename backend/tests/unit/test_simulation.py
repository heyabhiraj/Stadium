"""Unit tests for the stadium simulator."""

from stadiummind.simulation.stadium import StadiumSimulator


def test_tick_returns_reading_per_zone(venue):
    sim = StadiumSimulator(venue, seed=1)
    snapshot = sim.tick()
    assert set(snapshot) == set(z.id for z in venue)
    assert sim.minute == 1


def test_determinism_with_same_seed(venue):
    a = StadiumSimulator(build_seed_venue(), seed=99)
    b = StadiumSimulator(build_seed_venue(), seed=99)
    for _ in range(10):
        sa, sb = a.tick(), b.tick()
    assert {k: v.occupancy for k, v in sa.items()} == {
        k: v.occupancy for k, v in sb.items()
    }


def test_surge_increases_occupancy(venue):
    sim = StadiumSimulator(venue, seed=3)
    sim.warmup(3)
    before = sim.snapshot()["gate_3"].occupancy
    sim.inject_surge("gate_3", 3000)
    after = sim.tick()["gate_3"].occupancy
    assert after > before


def test_occupancy_never_negative_or_unbounded(venue):
    sim = StadiumSimulator(venue, seed=5)
    for _ in range(30):
        snap = sim.tick()
    for zone in venue:
        reading = snap[zone.id]
        assert reading.occupancy >= 0
        assert reading.occupancy <= zone.capacity * 1.2


def build_seed_venue():
    from stadiummind.core.venue import build_default_venue

    return build_default_venue()
