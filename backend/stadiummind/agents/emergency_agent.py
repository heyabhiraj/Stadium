"""Emergency agent: incident response, volunteer dispatch and fan rerouting.

When an incident is present in the context, this agent (a) recommends
dispatching medical/security volunteers to the affected zone using the LP
allocation routine, and (b) suggests an alternative walking path for nearby
fans so the response corridor stays clear.
"""

from __future__ import annotations

from stadiummind.agents.base import Agent, AgentContext
from stadiummind.core.models import (
    Incident,
    IncidentType,
    Recommendation,
    Severity,
    ZoneType,
)
from stadiummind.optimization.allocation import allocate_volunteers

# Severity -> weight used by the allocation objective.
_SEVERITY_WEIGHT = {
    Severity.LOW: 1.0,
    Severity.MEDIUM: 2.0,
    Severity.HIGH: 4.0,
    Severity.CRITICAL: 8.0,
}


class EmergencyAgent(Agent):
    name = "emergency"
    domain = "incident response & safety"

    def __init__(self, available_volunteers: int = 12) -> None:
        self.available_volunteers = available_volunteers

    def analyze(self, context: AgentContext) -> list[Recommendation]:
        incidents: list[Incident] = context.query.get("incidents", [])
        active = [i for i in incidents if not i.resolved]
        if not active:
            return []

        recs: list[Recommendation] = []

        # 1) Allocate volunteers across active incidents by severity weight.
        demands = {inc.zone_id: _SEVERITY_WEIGHT[inc.severity] for inc in active}
        allocation = allocate_volunteers(
            demands, available=self.available_volunteers, max_per_zone=6
        )

        for inc in active:
            zone = context.venue.get(inc.zone_id)
            assigned = allocation.get(inc.zone_id, 0)
            situation = (
                f"{inc.severity.value.upper()} {inc.type.value} incident at "
                f"{zone.name}: {inc.description}. "
                f"{assigned} volunteer(s) recommended for dispatch."
            )
            explanation = self.explain(
                context, situation, "How should the operations centre respond?"
            )
            recs.append(
                self._make_rec(
                    agent=self.name,
                    title=f"Dispatch {assigned} volunteer(s) to {zone.name}",
                    explanation=explanation,
                    confidence=0.9,
                    zone_id=inc.zone_id,
                    severity=inc.severity,
                    actions=[
                        f"Dispatch {assigned} volunteer(s) to {zone.name}",
                        (
                            "Notify medical team"
                            if inc.type is IncidentType.MEDICAL
                            else "Notify security team"
                        ),
                    ],
                    metadata={
                        "incident_id": inc.id,
                        "volunteers": assigned,
                    },
                )
            )

            # 2) Suggest a fan detour away from the incident corridor.
            detour = self._nearest_reroute_target(context, inc.zone_id)
            if detour is not None:
                recs.append(
                    self._make_rec(
                        agent=self.name,
                        title=f"Reroute fans away from {zone.name}",
                        explanation=(
                            f"Keep the response corridor to {zone.name} clear by "
                            f"guiding nearby fans toward {detour.name}."
                        ),
                        confidence=0.82,
                        zone_id=inc.zone_id,
                        severity=inc.severity,
                        actions=[f"Push detour alert toward {detour.name}"],
                        metadata={"incident_id": inc.id, "detour": detour.id},
                    )
                )
        return recs

    @staticmethod
    def _nearest_reroute_target(context: AgentContext, zone_id: str):
        """Pick the least-crowded neighbouring concourse/exit for a detour."""
        zone = context.venue.get(zone_id)
        neighbours = [context.venue.get(n) for n in zone.neighbours]
        candidates = [
            z
            for z in neighbours
            if z.type in (ZoneType.CONCOURSE, ZoneType.EXIT, ZoneType.GATE)
            and z.id in context.crowd
        ]
        if not candidates:
            return None
        return min(candidates, key=lambda z: context.crowd[z.id].ratio)
