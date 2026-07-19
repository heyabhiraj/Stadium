"""Sustainability agent: energy and waste optimisation hints.

Proactively suggests low-risk operational tweaks that reduce energy/resource
use when parts of the stadium are under-utilised (e.g. dimming lighting or
consolidating concessions in near-empty stands).
"""

from __future__ import annotations

from stadiummind.agents.base import Agent, AgentContext
from stadiummind.core.models import Recommendation, ZoneType

# Below this occupancy ratio a servable zone is considered under-utilised.
_UNDERUSE_RATIO = 0.15


class SustainabilityAgent(Agent):
    name = "sustainability"
    domain = "energy & resource efficiency"

    def analyze(self, context: AgentContext) -> list[Recommendation]:
        recs: list[Recommendation] = []
        servable = context.venue.of_type(ZoneType.FOOD) + context.venue.of_type(
            ZoneType.CONCOURSE
        )
        for zone in servable:
            reading = context.crowd.get(zone.id)
            if reading is None or reading.ratio > _UNDERUSE_RATIO:
                continue
            recs.append(
                self._make_rec(
                    agent=self.name,
                    title=f"Reduce power draw at {zone.name}",
                    explanation=(
                        f"{zone.name} is only {reading.ratio:.0%} occupied; dimming "
                        "lighting and pausing idle equipment saves energy with no "
                        "fan impact."
                    ),
                    confidence=0.65,
                    zone_id=zone.id,
                    actions=[f"Lower lighting/HVAC at {zone.name} by 30%"],
                    metadata={"occupancy_ratio": round(reading.ratio, 2)},
                )
            )
        return recs
