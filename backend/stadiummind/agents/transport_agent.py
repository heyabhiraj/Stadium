"""Transport agent: post-match egress and transport recommendations.

Recommends the best way home based on live transit/parking occupancy. Becomes
active in the final phase of the match (``match_minute`` late in the game or
after full time), matching the demo's closing beat.
"""

from __future__ import annotations

from stadiummind.agents.base import Agent, AgentContext
from stadiummind.core.models import Recommendation, ZoneType

# Match is considered "ending soon" after this many minutes.
_EGRESS_MINUTE = 85


class TransportAgent(Agent):
    name = "transport"
    domain = "egress & transport optimisation"
    intents = ("best_exit", "transport_home")

    def analyze(self, context: AgentContext) -> list[Recommendation]:
        if context.match_minute < _EGRESS_MINUTE:
            return []

        transit = context.venue.of_type(ZoneType.TRANSIT)
        parking = context.venue.of_type(ZoneType.PARKING)
        options = [z for z in transit + parking if z.id in context.crowd]
        if not options:
            return []

        best = min(options, key=lambda z: context.crowd[z.id].ratio)
        reading = context.crowd[best.id]
        situation = (
            f"Full time approaching (minute {context.match_minute}). "
            f"{best.name} is the least congested egress option at "
            f"{reading.ratio:.0%} occupancy."
        )
        explanation = self.explain(
            context, situation, "What is the best transport option for fans leaving?"
        )
        return [
            self._make_rec(
                agent=self.name,
                title=f"Recommend {best.name} for departure",
                explanation=explanation,
                confidence=0.85,
                zone_id=best.id,
                actions=[f"Promote {best.name} in fan app egress banner"],
                metadata={"option": best.id, "occupancy_ratio": round(reading.ratio, 2)},
            )
        ]

    def handle_query(self, context: AgentContext) -> Recommendation | None:
        proactive = self.analyze(
            # Force egress logic regardless of minute for a direct query.
            AgentContext(
                venue=context.venue,
                crowd=context.crowd,
                match_minute=max(context.match_minute, _EGRESS_MINUTE),
                llm=context.llm,
                predictor=context.predictor,
                routing=context.routing,
                settings=context.settings,
                query=context.query,
            )
        )
        return proactive[0] if proactive else None
