"""Walking-directions providers.

Real routing uses the **Google Maps Directions API** (walking mode) to route
between real coordinates (e.g. a fan's seat gate to the Meadowlands metro
station). When no Google key is configured, :class:`HaversineDirections`
returns a great-circle straight-line estimate so the feature still works
offline and in tests.

This complements the internal graph routing in ``optimization/routing.py``:
that engine handles *inside* the venue (congestion-aware, over the zone graph);
this provider handles *real-world* walking legs shown on the Google map.
"""

from __future__ import annotations

import logging
import math
import re
from dataclasses import dataclass, field

from stadiummind.core.config import Settings, get_settings

logger = logging.getLogger(__name__)

_DIRECTIONS_URL = "https://maps.googleapis.com/maps/api/directions/json"
_WALK_SPEED_M_PER_S = 1.4  # ~5 km/h


@dataclass
class DirectionsResult:
    """A normalised walking route between two real coordinates."""

    distance_m: float
    duration_min: float
    polyline: list[tuple[float, float]]  # ordered (lat, lng) points
    provider: str
    steps: list[str] = field(default_factory=list)


def haversine_m(a: tuple[float, float], b: tuple[float, float]) -> float:
    """Great-circle distance between two (lat, lng) points, in metres."""
    r = 6_371_000.0
    lat1, lng1 = map(math.radians, a)
    lat2, lng2 = map(math.radians, b)
    dlat, dlng = lat2 - lat1, lng2 - lng1
    h = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(dlng / 2) ** 2
    )
    return 2 * r * math.asin(math.sqrt(h))


class DirectionsProvider:
    """Abstract walking-directions source."""

    name = "abstract"

    def walking(
        self, origin: tuple[float, float], destination: tuple[float, float]
    ) -> DirectionsResult:  # pragma: no cover - abstract
        raise NotImplementedError


class HaversineDirections(DirectionsProvider):
    """Offline straight-line estimate (no external calls)."""

    name = "haversine"

    def walking(self, origin, destination) -> DirectionsResult:
        dist = haversine_m(origin, destination)
        return DirectionsResult(
            distance_m=round(dist, 1),
            duration_min=round(dist / _WALK_SPEED_M_PER_S / 60.0, 1),
            polyline=[origin, destination],
            provider=self.name,
            steps=[f"Walk ~{dist:.0f} m to your destination"],
        )


class GoogleDirectionsProvider(DirectionsProvider):
    """Walking directions from the Google Maps Directions API."""

    name = "google"

    def __init__(self, api_key: str, timeout: float = 8.0) -> None:
        self._api_key = api_key
        self._timeout = timeout
        self._fallback = HaversineDirections()

    def walking(self, origin, destination) -> DirectionsResult:
        try:
            return self._fetch(origin, destination)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Google Directions failed (%s); using haversine", exc)
            return self._fallback.walking(origin, destination)

    def _fetch(self, origin, destination) -> DirectionsResult:
        import httpx

        params = {
            "origin": f"{origin[0]},{origin[1]}",
            "destination": f"{destination[0]},{destination[1]}",
            "mode": "walking",
            "key": self._api_key,
        }
        with httpx.Client(timeout=self._timeout) as client:
            resp = client.get(_DIRECTIONS_URL, params=params)
            resp.raise_for_status()
            data = resp.json()

        if data.get("status") != "OK" or not data.get("routes"):
            raise ValueError(f"directions status={data.get('status')}")

        leg = data["routes"][0]["legs"][0]
        polyline = decode_polyline(data["routes"][0]["overview_polyline"]["points"])
        steps = [
            _strip_html(s.get("html_instructions", "")) for s in leg.get("steps", [])
        ]
        return DirectionsResult(
            distance_m=float(leg["distance"]["value"]),
            duration_min=round(leg["duration"]["value"] / 60.0, 1),
            polyline=polyline or [origin, destination],
            provider=self.name,
            steps=[s for s in steps if s],
        )


def decode_polyline(encoded: str) -> list[tuple[float, float]]:
    """Decode a Google encoded-polyline string to (lat, lng) points.

    Implements the standard polyline algorithm - no third-party dependency.
    """
    points: list[tuple[float, float]] = []
    index = lat = lng = 0
    length = len(encoded)
    while index < length:
        for is_lng in (False, True):
            shift = result = 0
            while True:
                b = ord(encoded[index]) - 63
                index += 1
                result |= (b & 0x1F) << shift
                shift += 5
                if b < 0x20:
                    break
            delta = ~(result >> 1) if result & 1 else (result >> 1)
            if is_lng:
                lng += delta
            else:
                lat += delta
        points.append((lat / 1e5, lng / 1e5))
    return points


def _strip_html(text: str) -> str:
    """Strip HTML tags from a Google instruction and collapse whitespace."""
    no_tags = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", no_tags).strip()


def build_directions_provider(settings: Settings | None = None) -> DirectionsProvider:
    """Factory: Google Directions when a key is set, else haversine."""
    settings = settings or get_settings()
    if settings.google_maps_api_key:
        return GoogleDirectionsProvider(
            settings.google_maps_api_key, timeout=settings.external_timeout_seconds
        )
    return HaversineDirections()
