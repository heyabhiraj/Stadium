"""The AI orchestrator.

Owns the registry of agents and coordinates two flows:

* **Proactive** (:meth:`analyze`) - build a shared :class:`AgentContext` from
  the current crowd snapshot and let every agent contribute recommendations,
  which are de-duplicated and ranked by ``severity x confidence``.
* **Reactive** (:meth:`handle_query`) - route a natural intent (e.g.
  ``navigate``) to the first agent that declares it can handle it.

Keeping this coordination in one place means adding a new capability is just
"write an Agent subclass and register it" - the Open/Closed principle in
practice.
"""

from __future__ import annotations

import logging

from stadiummind.agents.accessibility_agent import AccessibilityAgent
from stadiummind.agents.base import Agent, AgentContext
from stadiummind.agents.crowd_agent import CrowdAgent
from stadiummind.agents.emergency_agent import EmergencyAgent
from stadiummind.agents.navigation_agent import NavigationAgent
from stadiummind.agents.sustainability_agent import SustainabilityAgent
from stadiummind.agents.transport_agent import TransportAgent
from stadiummind.core.config import Settings, get_settings
from stadiummind.core.models import CrowdReading, Incident, Recommendation
from stadiummind.core.venue import Venue
from stadiummind.llm.adapter import LLMAdapter, build_llm
from stadiummind.ml.crowd_predictor import CrowdPredictor
from stadiummind.optimization.routing import RouteOptimizer

logger = logging.getLogger(__name__)

# Severity -> numeric rank used when ordering recommendations.
_SEVERITY_RANK = {"low": 1, "medium": 2, "high": 3, "critical": 4}


class AIOrchestrator:
    """Coordinates the pool of domain agents over a shared context."""

    def __init__(
        self,
        venue: Venue,
        llm: LLMAdapter | None = None,
        predictor: CrowdPredictor | None = None,
        settings: Settings | None = None,
        agents: list[Agent] | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.venue = venue
        self.llm = llm or build_llm(self.settings)
        self.predictor = predictor or CrowdPredictor()
        self.routing = RouteOptimizer(venue)
        # Default agent roster; callers may inject a custom list (e.g. tests).
        self.agents: list[Agent] = agents or [
            CrowdAgent(),
            NavigationAgent(),
            EmergencyAgent(),
            AccessibilityAgent(),
            TransportAgent(),
            SustainabilityAgent(),
        ]

    # ------------------------------------------------------------------ #
    # Context
    # ------------------------------------------------------------------ #
    def build_context(
        self,
        crowd: dict[str, CrowdReading],
        match_minute: int,
        incidents: list[Incident] | None = None,
        query: dict | None = None,
    ) -> AgentContext:
        merged_query = dict(query or {})
        # Incidents are passed to agents via the query bag to keep the context
        # signature stable across proactive and reactive flows.
        merged_query.setdefault("incidents", incidents or [])
        return AgentContext(
            venue=self.venue,
            crowd=crowd,
            match_minute=match_minute,
            llm=self.llm,
            predictor=self.predictor,
            routing=self.routing,
            settings=self.settings,
            query=merged_query,
        )

    # ------------------------------------------------------------------ #
    # Proactive analysis
    # ------------------------------------------------------------------ #
    def analyze(
        self,
        crowd: dict[str, CrowdReading],
        match_minute: int,
        incidents: list[Incident] | None = None,
    ) -> list[Recommendation]:
        """Run every agent and return ranked, de-duplicated recommendations."""
        context = self.build_context(crowd, match_minute, incidents)
        recommendations: list[Recommendation] = []
        for agent in self.agents:
            try:
                recommendations.extend(agent.analyze(context))
            except Exception:  # noqa: BLE001 - one failing agent must not stop others
                logger.exception("agent %s failed during analyze", agent.name)
        return self._rank(recommendations)

    # ------------------------------------------------------------------ #
    # Reactive query routing
    # ------------------------------------------------------------------ #
    def handle_query(
        self,
        intent: str,
        crowd: dict[str, CrowdReading],
        match_minute: int,
        params: dict | None = None,
    ) -> Recommendation | None:
        """Route ``intent`` to the first capable agent and return its answer."""
        context = self.build_context(crowd, match_minute, query=params or {})
        for agent in self.agents:
            if agent.can_handle(intent):
                try:
                    result = agent.handle_query(context)
                    if result is not None:
                        return result
                except Exception:  # noqa: BLE001
                    logger.exception("agent %s failed handling %s", agent.name, intent)
        return None

    def supported_intents(self) -> list[str]:
        """All intents any registered agent can handle (for the UI/help)."""
        intents: set[str] = set()
        for agent in self.agents:
            intents.update(agent.intents)
        return sorted(intents)

    # ------------------------------------------------------------------ #
    # Ranking
    # ------------------------------------------------------------------ #
    @staticmethod
    def _rank(recs: list[Recommendation]) -> list[Recommendation]:
        """Order by severity then confidence, dropping duplicate titles."""
        seen: set[str] = set()
        unique: list[Recommendation] = []
        for rec in recs:
            if rec.title in seen:
                continue
            seen.add(rec.title)
            unique.append(rec)
        return sorted(
            unique,
            key=lambda r: (_SEVERITY_RANK.get(r.severity.value, 0), r.confidence),
            reverse=True,
        )
