"""SQLAlchemy-backed :class:`Repository` implementation (optional).

Imported lazily by :func:`stadiummind.infra.repository.build_repository` only
when a ``DATABASE_URL`` is configured and SQLAlchemy is installed. Works with
both PostgreSQL (production) and SQLite (a lightweight local option).

This module is intentionally excluded from the default test run because it
requires SQLAlchemy and a database; it is covered by the optional
``tests/optional`` suite when the dependency is present.
"""

from __future__ import annotations

from sqlalchemy import Boolean, Column, Float, String, Text, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from stadiummind.core.models import (
    Incident,
    IncidentType,
    Recommendation,
    Severity,
)
from stadiummind.infra.repository import Repository

Base = declarative_base()


class _IncidentRow(Base):
    __tablename__ = "incidents"
    id = Column(String, primary_key=True)
    type = Column(String, nullable=False)
    severity = Column(String, nullable=False)
    zone_id = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    created_at = Column(Float, nullable=False)
    resolved = Column(Boolean, default=False)


class _RecommendationRow(Base):
    __tablename__ = "recommendations"
    id = Column(String, primary_key=True)
    agent = Column(String, nullable=False)
    title = Column(String, nullable=False)
    explanation = Column(Text, nullable=False)
    confidence = Column(Float, nullable=False)
    zone_id = Column(String, nullable=True)
    severity = Column(String, nullable=False)
    created_at = Column(Float, nullable=False)
    approved = Column(Boolean, nullable=True)


class SqlRepository(Repository):
    """Persist incidents and recommendations via SQLAlchemy ORM."""

    def __init__(self, database_url: str) -> None:
        self._engine = create_engine(database_url, future=True)
        Base.metadata.create_all(self._engine)
        self._Session = sessionmaker(bind=self._engine, future=True)

    # -- mapping helpers --------------------------------------------------
    @staticmethod
    def _to_incident(row: _IncidentRow) -> Incident:
        return Incident(
            id=row.id,
            type=IncidentType(row.type),
            severity=Severity(row.severity),
            zone_id=row.zone_id,
            description=row.description,
            created_at=row.created_at,
            resolved=row.resolved,
        )

    @staticmethod
    def _to_rec(row: _RecommendationRow) -> Recommendation:
        return Recommendation(
            id=row.id,
            agent=row.agent,
            title=row.title,
            explanation=row.explanation,
            confidence=row.confidence,
            zone_id=row.zone_id,
            severity=Severity(row.severity),
            created_at=row.created_at,
            approved=row.approved,
        )

    # -- incidents --------------------------------------------------------
    def save_incident(self, incident: Incident) -> Incident:
        with self._Session() as s:
            s.merge(
                _IncidentRow(
                    id=incident.id,
                    type=incident.type.value,
                    severity=incident.severity.value,
                    zone_id=incident.zone_id,
                    description=incident.description,
                    created_at=incident.created_at,
                    resolved=incident.resolved,
                )
            )
            s.commit()
        return incident

    def list_incidents(self, include_resolved: bool = True) -> list[Incident]:
        with self._Session() as s:
            q = s.query(_IncidentRow)
            if not include_resolved:
                q = q.filter(_IncidentRow.resolved.is_(False))
            rows = q.order_by(_IncidentRow.created_at.desc()).all()
        return [self._to_incident(r) for r in rows]

    def resolve_incident(self, incident_id: str) -> Incident | None:
        with self._Session() as s:
            row = s.get(_IncidentRow, incident_id)
            if row is None:
                return None
            row.resolved = True
            s.commit()
            return self._to_incident(row)

    # -- recommendations --------------------------------------------------
    def save_recommendation(self, rec: Recommendation) -> Recommendation:
        with self._Session() as s:
            s.merge(
                _RecommendationRow(
                    id=rec.id,
                    agent=rec.agent,
                    title=rec.title,
                    explanation=rec.explanation,
                    confidence=rec.confidence,
                    zone_id=rec.zone_id,
                    severity=rec.severity.value,
                    created_at=rec.created_at,
                    approved=rec.approved,
                )
            )
            s.commit()
        return rec

    def list_recommendations(self) -> list[Recommendation]:
        with self._Session() as s:
            rows = (
                s.query(_RecommendationRow)
                .order_by(_RecommendationRow.created_at.desc())
                .all()
            )
        return [self._to_rec(r) for r in rows]

    def set_recommendation_decision(
        self, rec_id: str, approved: bool
    ) -> Recommendation | None:
        with self._Session() as s:
            row = s.get(_RecommendationRow, rec_id)
            if row is None:
                return None
            row.approved = approved
            s.commit()
            return self._to_rec(row)
