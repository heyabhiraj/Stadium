"""Domain-specific exception hierarchy.

Using a small, well-defined exception tree (rather than raising bare
``Exception``) is a deliberate SDLC choice: callers can catch the precise
failure mode they care about, and the API layer can map each type onto a
sensible HTTP status code.
"""

from __future__ import annotations


class StadiumMindError(Exception):
    """Base class for every error raised inside StadiumMind AI."""


class ConfigurationError(StadiumMindError):
    """Raised when configuration/environment is invalid or incomplete."""


class AgentError(StadiumMindError):
    """Raised when an AI agent cannot produce a recommendation."""


class LLMError(StadiumMindError):
    """Raised when the underlying language model call fails."""


class OptimizationError(StadiumMindError):
    """Raised when an optimisation routine receives invalid input."""


class RepositoryError(StadiumMindError):
    """Raised for persistence-layer failures."""
