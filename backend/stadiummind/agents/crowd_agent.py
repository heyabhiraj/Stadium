"""Crowd agent: predicts congestion and recommends redirection.

This is the agent that drives the demo's core beat: it detects that a gate is
becoming congested (helped by the ML predictor and queueing theory), finds a
better alternative gate, and emits an *explained* recommendation for both the
operator and nearby fans.
"""

from __future__ import annotations

from stadiummind.agents.base import Agent, AgentContext
from stadiummind.core.models import Recommendation, Severity, ZoneType
from stadiummind.optimization.queueing import expected_wait_minutes

# Assumed throughput of a single turnstile: people served per minute.
_TURNSTILE_SERVICE_RATE = 8.0


class CrowdAgent(Agent):
    name = "crowd"
    domain = "crowd management & congestion prediction"

    def analyze(self, context: AgentContext) -> list[Recommendation]:
        recs: list[Recommendation] = []
        gates = context.venue.of_type(ZoneType.GATE)

        for gate in gates:
            reading = context.crowd.get(gate.id)
            if reading is None:
                continue

            wait = expected_wait_minutes(
                arrival_rate_per_min=reading.arrival_rate_per_min,
                service_rate_per_min_per_server=_TURNSTILE_SERVICE_RATE,
                servers=max(1, gate.service_points),
            )
            eta_to_congestion = context.predictor.predict_minutes_to_congestion(
                current_ratio=reading.ratio,
                arrival_rate_per_min=reading.arrival_rate_per_min,
                match_minute=context.match_minute,
                threshold=context.settings.congestion_threshold + 0.1,
            )

            # Raise a recommendation when the gate is already congested, the
            # current wait is high, or congestion is predicted imminently.
            trigger = (
                reading.ratio >= context.settings.congestion_threshold
                or wait >= context.settings.queue_alert_minutes
                or (eta_to_congestion is not None and eta_to_congestion <= 8)
            )
            if not trigger:
                continue

            alternative = self._best_alternative_gate(context, exclude=gate.id)
            if alternative is None:
                continue

            alt_reading = context.crowd[alternative.id]
            saved = max(0.0, wait - self._gate_wait(context, alternative))

            situation = (
                f"{gate.name} occupancy is {reading.ratio:.0%} with an estimated "
                f"{wait:.0f} min queue"
                + (
                    f"; congestion predicted in ~{eta_to_congestion} min"
                    if eta_to_congestion is not None
                    else ""
                )
                + f". {alternative.name} is only {alt_reading.ratio:.0%} full."
            )
            explanation = self.explain(
                context,
                situation,
                f"Should fans be redirected from {gate.name} to {alternative.name}?",
            )

            severity = Severity.HIGH if reading.ratio >= 0.9 else Severity.MEDIUM
            confidence = min(0.95, 0.6 + reading.ratio * 0.35)
            recs.append(
                self._make_rec(
                    agent=self.name,
                    title=f"Redirect fans from {gate.name} to {alternative.name}",
                    explanation=explanation,
                    confidence=confidence,
                    zone_id=gate.id,
                    severity=severity,
                    actions=[
                        f"Redirect arrivals to {alternative.name}",
                        f"Push alert to fans near {gate.name}",
                    ],
                    metadata={
                        "gate": gate.id,
                        "alternative": alternative.id,
                        "wait_minutes": round(wait, 1),
                        "eta_to_congestion_min": eta_to_congestion,
                        "minutes_saved": round(saved, 1),
                    },
                )
            )
        return recs

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #
    def _gate_wait(self, context: AgentContext, gate) -> float:
        reading = context.crowd[gate.id]
        return expected_wait_minutes(
            reading.arrival_rate_per_min,
            _TURNSTILE_SERVICE_RATE,
            max(1, gate.service_points),
        )

    def _best_alternative_gate(self, context: AgentContext, exclude: str):
        """Least-occupied gate other than ``exclude``."""
        candidates = [
            g
            for g in context.venue.of_type(ZoneType.GATE)
            if g.id != exclude and g.id in context.crowd
        ]
        if not candidates:
            return None
        return min(candidates, key=lambda g: context.crowd[g.id].ratio)
