"""Domain models shared across every layer.

These are plain, framework-agnostic dataclasses and enums. Keeping the domain
model independent of FastAPI/pydantic means the simulation, agents and
optimisation code can be unit-tested with no web framework in sight.
"""

from __future__ import annotations

import enum
import time
import uuid
from dataclasses import dataclass, field


class ZoneType(str, enum.Enum):
    """Categories of physical location inside/around the stadium."""

    GATE = "gate"
    SEATING = "seating"
    FOOD = "food"
    WASHROOM = "washroom"
    CONCOURSE = "concourse"
    MEDICAL = "medical"
    PARKING = "parking"
    TRANSIT = "transit"
    EXIT = "exit"


class CongestionLevel(str, enum.Enum):
    """Human-friendly congestion buckets used by the heatmap UI."""

    NORMAL = "normal"        # green
    MODERATE = "moderate"    # yellow
    BUSY = "busy"            # orange
    CONGESTED = "congested"  # red

    @classmethod
    def from_ratio(cls, ratio: float) -> "CongestionLevel":
        """Map an occupancy ratio (0-1) to a congestion bucket."""
        if ratio >= 0.90:
            return cls.CONGESTED
        if ratio >= 0.75:
            return cls.BUSY
        if ratio >= 0.50:
            return cls.MODERATE
        return cls.NORMAL


class IncidentType(str, enum.Enum):
    MEDICAL = "medical"
    SECURITY = "security"
    CROWD_CRUSH = "crowd_crush"
    FIRE = "fire"
    LOST_PERSON = "lost_person"


class Severity(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


def _new_id(prefix: str) -> str:
    """Generate a short, human-readable unique identifier."""
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


@dataclass
class Zone:
    """A physical zone in the stadium graph.

    ``x``/``y`` are normalised (0-1) coordinates used by the SVG map and by the
    routing engine to compute Euclidean walking distances.
    """

    id: str
    name: str
    type: ZoneType
    x: float
    y: float
    capacity: int
    # Number of parallel service points (turnstiles, tills, ...). Feeds the
    # queueing-theory model. ``0`` means the zone does not "serve" anyone.
    service_points: int = 0
    # Ids of directly reachable neighbouring zones (undirected graph edges).
    neighbours: list[str] = field(default_factory=list)
    accessible: bool = True  # step-free / wheelchair reachable
    # Real-world coordinates. Populated by the Venue geo-projection (or set
    # explicitly for landmarks such as the metro station). ``None`` until the
    # venue is anchored to a real location.
    lat: float | None = None
    lng: float | None = None


@dataclass
class CrowdReading:
    """A single occupancy sample for one zone at one point in time."""

    zone_id: str
    occupancy: int
    capacity: int
    arrival_rate_per_min: float
    timestamp: float = field(default_factory=time.time)

    @property
    def ratio(self) -> float:
        """Occupancy as a fraction of capacity, clamped to a sane range."""
        if self.capacity <= 0:
            return 0.0
        return max(0.0, min(occupancy_ratio(self.occupancy, self.capacity), 5.0))

    @property
    def level(self) -> CongestionLevel:
        return CongestionLevel.from_ratio(self.ratio)


def occupancy_ratio(occupancy: int, capacity: int) -> float:
    """Pure helper so the ratio maths can be unit-tested in isolation."""
    return occupancy / capacity if capacity else 0.0


@dataclass
class Route:
    """A walking route produced by the navigation/routing engine."""

    origin: str
    destination: str
    path: list[str]                 # ordered list of zone ids
    distance_m: float
    eta_minutes: float
    avoids_congestion: bool
    accessible: bool


@dataclass
class Incident:
    """An operational incident reported to the operations centre."""

    id: str
    type: IncidentType
    severity: Severity
    zone_id: str
    description: str
    created_at: float = field(default_factory=time.time)
    resolved: bool = False

    @classmethod
    def create(
        cls,
        type: IncidentType,
        severity: Severity,
        zone_id: str,
        description: str,
    ) -> "Incident":
        return cls(
            id=_new_id("inc"),
            type=type,
            severity=severity,
            zone_id=zone_id,
            description=description,
        )


@dataclass
class Recommendation:
    """The unit of output of the AI layer.

    Embodies the product principle *"explain before recommending"*: every
    recommendation carries a human-readable ``explanation`` and a numeric
    ``confidence`` and always requires human approval before it is actioned.
    """

    id: str
    agent: str                       # which agent produced it
    title: str                       # short action, e.g. "Open Gate 5"
    explanation: str                 # why - shown to the operator/fan
    confidence: float                # 0-1
    zone_id: str | None = None
    severity: Severity = Severity.LOW
    actions: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    approved: bool | None = None     # None = pending, True/False = decided

    @classmethod
    def create(
        cls,
        agent: str,
        title: str,
        explanation: str,
        confidence: float,
        *,
        id: str | None = None,
        **kwargs,
    ) -> "Recommendation":
        confidence = max(0.0, min(confidence, 1.0))
        # A deterministic id (derived from agent + title + zone) makes
        # recommendations idempotent: re-analysing the same situation upserts
        # the existing record instead of creating an unbounded stream of
        # duplicates, and lets an operator's approve/reject decision persist
        # across polling cycles.
        rec_id = id or stable_recommendation_id(
            agent, title, kwargs.get("zone_id")
        )
        return cls(
            id=rec_id,
            agent=agent,
            title=title,
            explanation=explanation,
            confidence=confidence,
            **kwargs,
        )


def stable_recommendation_id(agent: str, title: str, zone_id: str | None) -> str:
    """Deterministic id for a recommendation, based on its identity."""
    import hashlib

    signature = f"{agent}|{title}|{zone_id or ''}"
    return "rec_" + hashlib.sha1(signature.encode()).hexdigest()[:12]


@dataclass
class Match:
    """A football match, as surfaced on the fan home screen.

    Normalised so the UI never depends on a specific data provider's JSON
    shape. ``source`` records where the data came from ("football-data" or
    "mock") for observability.
    """

    id: str
    home_team: str
    away_team: str
    competition: str
    venue: str
    kickoff_utc: str | None          # ISO-8601 timestamp
    status: str                      # SCHEDULED | LIVE | IN_PLAY | FINISHED ...
    home_score: int | None = None
    away_score: int | None = None
    minute: int | None = None
    source: str = "mock"


@dataclass
class Alert:
    """A lightweight notification surfaced to fans and operators."""

    id: str
    message: str
    zone_id: str | None
    level: CongestionLevel
    created_at: float = field(default_factory=time.time)

    @classmethod
    def create(
        cls, message: str, level: CongestionLevel, zone_id: str | None = None
    ) -> "Alert":
        return cls(id=_new_id("alert"), message=message, zone_id=zone_id, level=level)
