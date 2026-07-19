"""Navigation agent: reactive wayfinding for fans.

Answers "how do I get from A to B?" queries, honouring the fan's "avoid crowd"
and accessibility preferences by delegating to the :class:`RouteOptimizer`.
"""

from __future__ import annotations

from stadiummind.agents.base import Agent, AgentContext
from stadiummind.core.models import Recommendation


class NavigationAgent(Agent):
    name = "navigation"
    domain = "indoor wayfinding & routing"
    intents = ("navigate", "find_seat", "find_food", "find_washroom", "find_exit")

    def analyze(self, context: AgentContext) -> list[Recommendation]:
        # Navigation is reactive only; it does not push proactive recs.
        return []

    def handle_query(self, context: AgentContext) -> Recommendation | None:
        origin = context.query.get("origin")
        destination = context.query.get("destination")
        if not origin or not destination:
            return None
        if origin not in context.venue or destination not in context.venue:
            return None

        avoid = bool(context.query.get("avoid_congestion", True))
        accessible = bool(context.query.get("accessible", False))
        try:
            route = context.routing.route(
                origin,
                destination,
                crowd=context.crowd,
                avoid_congestion=avoid,
                accessible_only=accessible,
            )
        except (ValueError, KeyError):
            return None

        dest_name = context.venue.get(destination).name
        readable_path = " -> ".join(context.venue.get(z).name for z in route.path)
        situation = (
            f"Route to {dest_name}: {readable_path}. "
            f"{route.distance_m:.0f} m, about {route.eta_minutes:.0f} min walking"
            + (", avoiding congested zones" if avoid else "")
            + (", step-free" if accessible else "")
            + "."
        )
        explanation = self.explain(
            context, situation, f"What is the best walking route to {dest_name}?"
        )
        return self._make_rec(
            agent=self.name,
            title=f"Route to {dest_name} ({route.eta_minutes:.0f} min)",
            explanation=explanation,
            confidence=0.9,
            zone_id=destination,
            actions=["Start navigation"],
            metadata={
                "path": route.path,
                "distance_m": route.distance_m,
                "eta_minutes": route.eta_minutes,
                "accessible": route.accessible,
                "avoids_congestion": route.avoids_congestion,
            },
        )
