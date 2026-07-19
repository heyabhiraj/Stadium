"""Application service layer (composition root).

:class:`StadiumService` wires together the simulator, orchestrator, repository,
cache and message bus, and exposes coarse-grained use-cases that the HTTP layer
calls. Concentrating composition here keeps the FastAPI routes thin and makes
the whole system easy to instantiate in a test with a single line.
"""

from __future__ import annotations

import logging
import threading

from stadiummind.agents.orchestrator import AIOrchestrator
from stadiummind.core.config import Settings, get_settings
from stadiummind.core.models import (
    Alert,
    CrowdReading,
    Incident,
    IncidentType,
    Match,
    Recommendation,
    Severity,
)
from stadiummind.core.venue import build_default_venue
from stadiummind.infra import (
    build_key_value_store,
    build_message_bus,
    build_repository,
)
from stadiummind.integrations.directions import (
    DirectionsResult,
    build_directions_provider,
)
from stadiummind.integrations.matches import build_match_provider
from stadiummind.simulation.stadium import StadiumSimulator

logger = logging.getLogger(__name__)

# Message-bus topics.
TOPIC_CROWD = "crowd.readings"
TOPIC_RECS = "ai.recommendations"
TOPIC_INCIDENTS = "ops.incidents"

# Cache key for the latest crowd snapshot.
_CACHE_SNAPSHOT = "crowd:latest"


class StadiumService:
    """The single object the API depends on."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.venue = build_default_venue()
        self.simulator = StadiumSimulator(
            self.venue, seed=self.settings.simulation_seed
        )
        self.orchestrator = AIOrchestrator(self.venue, settings=self.settings)
        self.repository = build_repository(self.settings)
        self.cache = build_key_value_store(self.settings)
        self.bus = build_message_bus(self.settings)
        self.match_provider = build_match_provider(self.settings)
        self.directions_provider = build_directions_provider(self.settings)
        self.match_minute = 0
        # Guards all mutable simulation/service state so the WebSocket tick loop
        # and concurrent HTTP requests (FastAPI threadpool) cannot race.
        self._lock = threading.RLock()
        # Warm the stadium up to a realistic pre-match crowd. We keep the most
        # recent snapshot so the live view reflects real arrival rates
        # (including surges and their decay) rather than a recomputed baseline.
        self.simulator.warmup(minutes=5)
        self._last_snapshot: dict[str, CrowdReading] = self.simulator.snapshot()
        self._publish_snapshot(self._last_snapshot)

    # ------------------------------------------------------------------ #
    # Crowd
    # ------------------------------------------------------------------ #
    def tick(self) -> dict[str, CrowdReading]:
        """Advance the simulation one minute and publish the new snapshot."""
        with self._lock:
            self.match_minute += 1
            self._last_snapshot = self.simulator.tick()
            self._publish_snapshot(self._last_snapshot)
            return self._last_snapshot

    def current_snapshot(self) -> dict[str, CrowdReading]:
        """Return the most recent snapshot (reflects surges and their decay)."""
        with self._lock:
            return self._last_snapshot

    def inject_surge(self, zone_id: str, people: int) -> None:
        """Force a crowd surge (used by the demo to trigger congestion)."""
        if people <= 0:
            raise ValueError("surge size must be a positive number of people")
        with self._lock:
            self.simulator.inject_surge(zone_id, people)

    def heatmap(self) -> list[dict]:
        """Return per-zone data shaped for the heatmap / SVG + Google map UI."""
        snapshot = self.current_snapshot()
        result = []
        for zone in self.venue:
            reading = snapshot[zone.id]
            result.append(
                {
                    "id": zone.id,
                    "name": zone.name,
                    "type": zone.type.value,
                    "x": zone.x,
                    "y": zone.y,
                    "lat": zone.lat,
                    "lng": zone.lng,
                    "occupancy": reading.occupancy,
                    "capacity": zone.capacity,
                    "ratio": round(reading.ratio, 3),
                    "level": reading.level.value,
                    "accessible": zone.accessible,
                }
            )
        return result

    # ------------------------------------------------------------------ #
    # Match data (external)
    # ------------------------------------------------------------------ #
    def match(self) -> Match:
        """Return the current match from the configured provider."""
        return self.match_provider.current_match()

    # ------------------------------------------------------------------ #
    # Real-world walking directions (external)
    # ------------------------------------------------------------------ #
    def directions(self, origin_zone: str, dest_zone: str) -> DirectionsResult:
        """Walking directions between two zones' real coordinates."""
        if origin_zone not in self.venue or dest_zone not in self.venue:
            raise KeyError("origin/destination must be known zones")
        a = self.venue.get(origin_zone)
        b = self.venue.get(dest_zone)
        if None in (a.lat, a.lng, b.lat, b.lng):
            raise ValueError("zones are not geo-located")
        return self.directions_provider.walking((a.lat, a.lng), (b.lat, b.lng))

    @property
    def maps_enabled(self) -> bool:
        return self.directions_provider.name == "google"

    # ------------------------------------------------------------------ #
    # AI
    # ------------------------------------------------------------------ #
    def recommendations(self) -> list[Recommendation]:
        """Run proactive analysis, persist and publish the results.

        Recommendations have deterministic ids, so re-analysing the same
        situation upserts rather than duplicates. Any prior approve/reject
        decision is carried forward so an operator's choice is never lost by a
        subsequent polling cycle.
        """
        with self._lock:
            snapshot = self._last_snapshot
            minute = self.match_minute
            incidents = self.repository.list_incidents(include_resolved=False)
            existing = {r.id: r for r in self.repository.list_recommendations()}
            recs = self.orchestrator.analyze(snapshot, minute, incidents)
            for rec in recs:
                prior = existing.get(rec.id)
                if prior is not None and prior.approved is not None:
                    rec.approved = prior.approved  # preserve operator decision
                self.repository.save_recommendation(rec)
                self.bus.publish(TOPIC_RECS, {"id": rec.id, "title": rec.title})
            return recs

    def ask(self, intent: str, params: dict | None = None) -> Recommendation | None:
        """Handle a reactive fan/operator query."""
        snapshot = self.current_snapshot()
        return self.orchestrator.handle_query(
            intent, snapshot, self.match_minute, params
        )

    def supported_intents(self) -> list[str]:
        return self.orchestrator.supported_intents()

    def decide(self, rec_id: str, approved: bool) -> Recommendation | None:
        """Record an operator's approve/reject decision (human-in-the-loop)."""
        return self.repository.set_recommendation_decision(rec_id, approved)

    # ------------------------------------------------------------------ #
    # Incidents
    # ------------------------------------------------------------------ #
    def report_incident(
        self,
        type: IncidentType,
        severity: Severity,
        zone_id: str,
        description: str,
    ) -> Incident:
        if zone_id not in self.venue:
            raise KeyError(f"unknown zone {zone_id!r}")
        incident = Incident.create(type, severity, zone_id, description)
        self.repository.save_incident(incident)
        self.bus.publish(TOPIC_INCIDENTS, {"id": incident.id, "zone": zone_id})
        return incident

    def list_incidents(self, include_resolved: bool = True) -> list[Incident]:
        return self.repository.list_incidents(include_resolved)

    def resolve_incident(self, incident_id: str) -> Incident | None:
        return self.repository.resolve_incident(incident_id)

    # ------------------------------------------------------------------ #
    # Alerts (derived from the snapshot)
    # ------------------------------------------------------------------ #
    def alerts(self) -> list[Alert]:
        """Surface congested zones as fan-facing alerts."""
        alerts: list[Alert] = []
        snapshot = self.current_snapshot()
        for zone in self.venue:
            reading = snapshot[zone.id]
            if reading.ratio >= self.settings.congestion_threshold:
                alerts.append(
                    Alert.create(
                        message=f"{zone.name} is {reading.level.value}",
                        level=reading.level,
                        zone_id=zone.id,
                    )
                )
        return alerts

    # ------------------------------------------------------------------ #
    # Internals
    # ------------------------------------------------------------------ #
    def _publish_snapshot(self, snapshot: dict[str, CrowdReading]) -> None:
        payload = {
            zid: {"occupancy": r.occupancy, "ratio": round(r.ratio, 3)}
            for zid, r in snapshot.items()
        }
        self.cache.set(_CACHE_SNAPSHOT, payload, ttl_seconds=60)
        self.bus.publish(TOPIC_CROWD, {"minute": self.match_minute, "zones": payload})
