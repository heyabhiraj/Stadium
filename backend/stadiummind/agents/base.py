"""Abstract base class and shared context for all AI agents.

The base class encodes the contract every agent honours and centralises the
"explain before recommending" behaviour so subclasses stay small and focused
on their own domain logic. This is the Template-Method + Strategy pattern:
subclasses fill in :meth:`analyze` / :meth:`handle_query`; the base class
provides the LLM-backed :meth:`explain` helper they all reuse.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from stadiummind.core.config import Settings, get_settings
from stadiummind.core.models import CrowdReading, Recommendation
from stadiummind.core.venue import Venue
from stadiummind.llm.adapter import LLMAdapter
from stadiummind.ml.crowd_predictor import CrowdPredictor
from stadiummind.optimization.routing import RouteOptimizer


@dataclass
class AgentContext:
    """Everything an agent needs to reason about the current moment.

    A single context object is built once per orchestration cycle and shared
    (read-only by convention) across every agent, which keeps analysis cheap
    and consistent.
    """

    venue: Venue
    crowd: dict[str, CrowdReading]
    match_minute: int
    llm: LLMAdapter
    predictor: CrowdPredictor
    routing: RouteOptimizer
    settings: Settings = field(default_factory=get_settings)
    # Free-form parameters for a reactive query (origin, destination, text...).
    query: dict = field(default_factory=dict)


class Agent(ABC):
    """Base class for a single-domain reasoning agent."""

    #: Unique agent name (used in logs, API payloads and recommendation.agent).
    name: str = "agent"
    #: Human-readable domain description.
    domain: str = "generic"
    #: Query intents this agent can answer reactively.
    intents: tuple[str, ...] = ()

    @abstractmethod
    def analyze(self, context: AgentContext) -> list[Recommendation]:
        """Proactively inspect the context and return zero or more recs."""

    def can_handle(self, intent: str) -> bool:
        """Whether this agent can answer a reactive query of ``intent``."""
        return intent in self.intents

    def handle_query(self, context: AgentContext) -> Recommendation | None:
        """Answer a reactive query. Default: no reactive capability."""
        return None

    # ------------------------------------------------------------------ #
    # Shared helpers
    # ------------------------------------------------------------------ #
    def explain(self, context: AgentContext, situation: str, question: str) -> str:
        """Produce a human-readable explanation via the LLM adapter.

        Falls back to the raw situation string if the LLM raises, so an agent
        always returns *something* explanatory even during an LLM outage.
        """
        try:
            return context.llm.explain(situation, question)
        except Exception:  # noqa: BLE001 - never let explanation break analysis
            return situation

    @staticmethod
    def _make_rec(agent: str, title: str, explanation: str, confidence: float, **kw):
        return Recommendation.create(
            agent=agent,
            title=title,
            explanation=explanation,
            confidence=confidence,
            **kw,
        )
