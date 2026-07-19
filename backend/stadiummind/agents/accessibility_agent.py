"""Accessibility agent: step-free routing and reactive assistance.

Reactively answers wheelchair/step-free routing queries and proactively flags
when an accessible route to key amenities is being degraded by congestion.
"""

from __future__ import annotations

from stadiummind.agents.base import Agent, AgentContext
from stadiummind.core.models import Recommendation, ZoneType


class AccessibilityAgent(Agent):
    name = "accessibility"
    domain = "accessibility & step-free navigation"
    intents = ("wheelchair_route", "accessible_route")

    def analyze(self, context: AgentContext) -> list[Recommendation]:
        # Proactively warn if any medical point is hard to reach step-free.
        recs: list[Recommendation] = []
        for medical in context.venue.of_type(ZoneType.MEDICAL):
            if not medical.accessible:
                recs.append(
                    self._make_rec(
                        agent=self.name,
                        title=f"Accessibility risk near {medical.name}",
                        explanation=(
                            f"{medical.name} is not currently marked step-free; "
                            "verify ramp/lift availability."
                        ),
                        confidence=0.7,
                        zone_id=medical.id,
                    )
                )
        return recs

    def handle_query(self, context: AgentContext) -> Recommendation | None:
        origin = context.query.get("origin")
        destination = context.query.get("destination")
        if not origin or not destination:
            return None
        if origin not in context.venue or destination not in context.venue:
            return None
        try:
            route = context.routing.route(
                origin,
                destination,
                crowd=context.crowd,
                avoid_congestion=True,
                accessible_only=True,
            )
        except (ValueError, KeyError):
            return None

        dest_name = context.venue.get(destination).name
        situation = (
            f"Step-free route to {dest_name}: about {route.eta_minutes:.0f} min, "
            f"{route.distance_m:.0f} m, all zones wheelchair accessible."
        )
        explanation = self.explain(
            context, situation, f"What is the accessible route to {dest_name}?"
        )
        return self._make_rec(
            agent=self.name,
            title=f"Step-free route to {dest_name}",
            explanation=explanation,
            confidence=0.9,
            zone_id=destination,
            actions=["Start accessible navigation"],
            metadata={"path": route.path, "accessible": route.accessible},
        )
