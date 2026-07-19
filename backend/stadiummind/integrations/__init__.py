"""External API integrations (match data, maps directions).

Each integration follows the same Strategy pattern used across the codebase: a
small abstract interface, a real HTTP-backed implementation selected when a key
is configured, and a deterministic offline fallback used otherwise (and in
tests).
"""

from stadiummind.integrations.directions import (
    DirectionsProvider,
    GoogleDirectionsProvider,
    HaversineDirections,
    build_directions_provider,
)
from stadiummind.integrations.matches import (
    FootballDataProvider,
    MatchProvider,
    MockMatchProvider,
    build_match_provider,
)

__all__ = [
    "MatchProvider",
    "MockMatchProvider",
    "FootballDataProvider",
    "build_match_provider",
    "DirectionsProvider",
    "GoogleDirectionsProvider",
    "HaversineDirections",
    "build_directions_provider",
]
