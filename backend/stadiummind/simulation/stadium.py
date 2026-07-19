"""A deterministic, discrete-time crowd simulator.

Because a hackathon demo has no real turnstile sensors, the simulator *is* the
data source. It advances the stadium in fixed ticks (each tick == one
simulated minute) and produces a fresh :class:`CrowdReading` per zone.

Dynamics
--------
Each zone has a *target* occupancy ratio that depends on its type and on how
close the match is to kickoff (stands fill up as kickoff approaches). Occupancy
relaxes smoothly toward that target with a little noise, which keeps baseline
occupancy realistic and *non-saturating* - so an injected surge produces a
clearly distinguishable hotspot rather than everything pinning at capacity.

Design notes
------------
* Deterministic: a seeded RNG makes every run reproducible - exactly what makes
  the demo and the tests reliable.
* Scriptable: :meth:`inject_surge` lets the demo force congestion at a chosen
  gate ("two buses just arrived at Gate 3"), which is what triggers the agents.
* Pure state transition: :meth:`tick` returns the new snapshot and performs no
  I/O, so it is trivially unit-testable.
"""

from __future__ import annotations

import random

from stadiummind.core.models import CrowdReading, ZoneType
from stadiummind.core.venue import Venue, build_default_venue

# Baseline target occupancy ratio by zone type (pre-kickoff, 0-1).
_TARGET_RATIO: dict[ZoneType, float] = {
    ZoneType.GATE: 0.30,
    ZoneType.CONCOURSE: 0.35,
    ZoneType.SEATING: 0.20,  # grows toward kickoff (see _target_ratio)
    ZoneType.FOOD: 0.45,
    ZoneType.WASHROOM: 0.40,
    ZoneType.MEDICAL: 0.08,
    ZoneType.PARKING: 0.55,
    ZoneType.TRANSIT: 0.40,
    ZoneType.EXIT: 0.10,
}

# How fast occupancy relaxes toward its target each tick (0-1).
_RELAX = 0.35
# Per-tick surge decay factor.
_SURGE_DECAY = 0.6
# Hard clamp: occupancy may transiently exceed capacity by this factor.
_MAX_OVER_CAPACITY = 1.2


class StadiumSimulator:
    """Simulates occupancy across every zone of a :class:`Venue`."""

    def __init__(self, venue: Venue | None = None, seed: int = 42) -> None:
        self.venue = venue or build_default_venue()
        self._rng = random.Random(seed)
        self.minute = 0
        self._occupancy: dict[str, int] = {z.id: 0 for z in self.venue}
        # Pending transient surges per zone (applied next tick, then decayed).
        self._surges: dict[str, int] = {}

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #
    def inject_surge(self, zone_id: str, people: int) -> None:
        """Add a transient crowd surge to a zone (e.g. arriving buses)."""
        if zone_id not in self.venue:
            raise KeyError(f"unknown zone {zone_id!r}")
        self._surges[zone_id] = self._surges.get(zone_id, 0) + int(people)

    def tick(self) -> dict[str, CrowdReading]:
        """Advance the simulation by one minute and return a fresh snapshot."""
        self.minute += 1
        snapshot: dict[str, CrowdReading] = {}

        for zone in self.venue:
            target = self._target_ratio(zone.type) * zone.capacity
            current = self._occupancy[zone.id]

            # Smooth relaxation toward the target plus mild noise.
            drift = (target - current) * _RELAX
            noise = self._rng.gauss(0, zone.capacity * 0.01)
            surge = self._surges.get(zone.id, 0)

            new_occ = int(current + drift + noise + surge)
            new_occ = max(0, min(new_occ, int(zone.capacity * _MAX_OVER_CAPACITY)))
            self._occupancy[zone.id] = new_occ

            # Arrival rate (people/min) drives the queueing model. It reflects
            # positive inflow this tick plus any surge - so a surge spikes it.
            inflow = max(0.0, drift) + surge
            snapshot[zone.id] = CrowdReading(
                zone_id=zone.id,
                occupancy=new_occ,
                capacity=zone.capacity,
                arrival_rate_per_min=round(inflow, 2),
            )

        self._decay_surges()
        return snapshot

    def snapshot(self) -> dict[str, CrowdReading]:
        """Return the current occupancy without advancing time."""
        return {
            zone.id: CrowdReading(
                zone_id=zone.id,
                occupancy=self._occupancy[zone.id],
                capacity=zone.capacity,
                arrival_rate_per_min=self._baseline_inflow(zone),
            )
            for zone in self.venue
        }

    def warmup(self, minutes: int) -> None:
        """Run ``minutes`` ticks to reach a realistic pre-match state."""
        for _ in range(max(0, minutes)):
            self.tick()

    # ------------------------------------------------------------------ #
    # Internals
    # ------------------------------------------------------------------ #
    def _target_ratio(self, zone_type: ZoneType) -> float:
        """Target occupancy ratio, with stands filling up toward kickoff."""
        base = _TARGET_RATIO.get(zone_type, 0.2)
        if zone_type is ZoneType.SEATING:
            # Ramp from ~0.2 up to ~0.9 over the first 45 simulated minutes.
            base = min(0.9, 0.2 + 0.015 * self.minute)
        return base

    def _baseline_inflow(self, zone) -> float:
        """A representative steady-state inflow used by :meth:`snapshot`."""
        target = self._target_ratio(zone.type) * zone.capacity
        return round(max(0.0, (target - self._occupancy[zone.id]) * _RELAX), 2)

    def _decay_surges(self) -> None:
        """Surges dissipate each tick until they vanish."""
        decayed: dict[str, int] = {}
        for zone_id, amount in self._surges.items():
            remaining = int(amount * _SURGE_DECAY)
            if remaining > 0:
                decayed[zone_id] = remaining
        self._surges = decayed
