"""Persistence abstraction for incidents and recommendations.

The :class:`Repository` interface hides the storage backend. The default
implementation is a thread-safe in-memory store (perfect for the demo and for
tests). A SQLAlchemy implementation is provided for PostgreSQL/SQLite when a
``DATABASE_URL`` is configured; it is created lazily so the heavy dependency is
only imported when actually needed.
"""

from __future__ import annotations

import logging
import threading
from abc import ABC, abstractmethod

from stadiummind.core.config import Settings
from stadiummind.core.models import Incident, Recommendation

logger = logging.getLogger(__name__)


class Repository(ABC):
    """Abstract store for the two persisted aggregates."""

    @abstractmethod
    def save_incident(self, incident: Incident) -> Incident: ...

    @abstractmethod
    def list_incidents(self, include_resolved: bool = True) -> list[Incident]: ...

    @abstractmethod
    def resolve_incident(self, incident_id: str) -> Incident | None: ...

    @abstractmethod
    def save_recommendation(self, rec: Recommendation) -> Recommendation: ...

    @abstractmethod
    def list_recommendations(self) -> list[Recommendation]: ...

    @abstractmethod
    def set_recommendation_decision(
        self, rec_id: str, approved: bool
    ) -> Recommendation | None: ...


class InMemoryRepository(Repository):
    """Thread-safe in-process repository backed by ordered dicts."""

    def __init__(self) -> None:
        self._incidents: dict[str, Incident] = {}
        self._recs: dict[str, Recommendation] = {}
        self._lock = threading.RLock()

    def save_incident(self, incident: Incident) -> Incident:
        with self._lock:
            self._incidents[incident.id] = incident
        return incident

    def list_incidents(self, include_resolved: bool = True) -> list[Incident]:
        with self._lock:
            items = list(self._incidents.values())
        if not include_resolved:
            items = [i for i in items if not i.resolved]
        return sorted(items, key=lambda i: i.created_at, reverse=True)

    def resolve_incident(self, incident_id: str) -> Incident | None:
        with self._lock:
            incident = self._incidents.get(incident_id)
            if incident is not None:
                incident.resolved = True
        return incident

    def save_recommendation(self, rec: Recommendation) -> Recommendation:
        with self._lock:
            self._recs[rec.id] = rec
        return rec

    def list_recommendations(self) -> list[Recommendation]:
        with self._lock:
            items = list(self._recs.values())
        return sorted(items, key=lambda r: r.created_at, reverse=True)

    def set_recommendation_decision(
        self, rec_id: str, approved: bool
    ) -> Recommendation | None:
        with self._lock:
            rec = self._recs.get(rec_id)
            if rec is not None:
                rec.approved = approved
        return rec


def build_repository(settings: Settings) -> Repository:
    """Return a SQL repository when configured/available, else in-memory.

    The SQL implementation lives in :mod:`stadiummind.infra.sql_repository` and
    is imported lazily to keep SQLAlchemy optional.
    """
    if settings.database_url:
        try:
            from stadiummind.infra.sql_repository import SqlRepository

            return SqlRepository(settings.database_url)
        except Exception:  # noqa: BLE001
            logger.warning("SQL backend unavailable; using in-memory repository")
    return InMemoryRepository()
