"""Pydantic request/response schemas for the HTTP API.

Keeping the wire schemas separate from the domain dataclasses lets the two
evolve independently and gives FastAPI clean OpenAPI documentation.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from stadiummind.core.models import (
    Incident,
    IncidentType,
    Match,
    Recommendation,
    Severity,
)


class LoginRequest(BaseModel):
    username: str
    role: str = Field(default="fan")


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str


class ZoneHeat(BaseModel):
    id: str
    name: str
    type: str
    x: float
    y: float
    lat: float | None = None
    lng: float | None = None
    occupancy: int
    capacity: int
    ratio: float
    level: str
    accessible: bool


class MatchOut(BaseModel):
    id: str
    home_team: str
    away_team: str
    competition: str
    venue: str
    kickoff_utc: str | None
    status: str
    home_score: int | None
    away_score: int | None
    minute: int | None
    source: str

    @classmethod
    def from_domain(cls, m: Match) -> "MatchOut":
        return cls(**m.__dict__)


class DirectionsOut(BaseModel):
    origin: str
    destination: str
    distance_m: float
    duration_min: float
    provider: str
    polyline: list[list[float]]      # [[lat, lng], ...]
    steps: list[str]


class RecommendationOut(BaseModel):
    id: str
    agent: str
    title: str
    explanation: str
    confidence: float
    zone_id: str | None
    severity: str
    actions: list[str]
    metadata: dict
    approved: bool | None

    @classmethod
    def from_domain(cls, rec: Recommendation) -> "RecommendationOut":
        return cls(
            id=rec.id,
            agent=rec.agent,
            title=rec.title,
            explanation=rec.explanation,
            confidence=round(rec.confidence, 3),
            zone_id=rec.zone_id,
            severity=rec.severity.value,
            actions=rec.actions,
            metadata=rec.metadata,
            approved=rec.approved,
        )


class QueryRequest(BaseModel):
    intent: str
    params: dict = Field(default_factory=dict)


class IncidentRequest(BaseModel):
    type: IncidentType
    severity: Severity
    zone_id: str
    description: str


class IncidentOut(BaseModel):
    id: str
    type: str
    severity: str
    zone_id: str
    description: str
    resolved: bool

    @classmethod
    def from_domain(cls, inc: Incident) -> "IncidentOut":
        return cls(
            id=inc.id,
            type=inc.type.value,
            severity=inc.severity.value,
            zone_id=inc.zone_id,
            description=inc.description,
            resolved=inc.resolved,
        )


class DecisionRequest(BaseModel):
    approved: bool


class AlertOut(BaseModel):
    id: str
    message: str
    zone_id: str | None
    level: str
