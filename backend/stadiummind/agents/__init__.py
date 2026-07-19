"""The OOP multi-agent orchestrator ("the AI brain").

Each domain (crowd, navigation, emergency, ...) is owned by an :class:`Agent`
subclass. The :class:`AIOrchestrator` fans a shared :class:`AgentContext` out
to every agent for proactive analysis and routes fan/operator queries to the
agent best able to answer them.
"""

from stadiummind.agents.base import Agent, AgentContext
from stadiummind.agents.orchestrator import AIOrchestrator

__all__ = ["Agent", "AgentContext", "AIOrchestrator"]
