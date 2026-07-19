"""FastAPI application factory.

Exposes the gateway described in the architecture (auth, maps, crowd, AI,
incidents, notifications) plus a WebSocket live feed. The factory pattern
(:func:`create_app`) lets tests inject a pre-seeded :class:`StadiumService`.
"""

from __future__ import annotations

import asyncio
import logging

from fastapi import Depends, FastAPI, Header, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from stadiummind.api.schemas import (
    AlertOut,
    DecisionRequest,
    DirectionsOut,
    IncidentOut,
    IncidentRequest,
    LoginRequest,
    MatchOut,
    QueryRequest,
    RecommendationOut,
    TokenResponse,
    ZoneHeat,
)
from stadiummind.api.security import AuthError, issue_token, verify_token
from stadiummind.api.service import StadiumService
from stadiummind.core.config import get_settings

logger = logging.getLogger(__name__)


def create_app(service: StadiumService | None = None) -> FastAPI:
    """Build and return the FastAPI application."""
    settings = get_settings()
    service = service or StadiumService(settings)

    app = FastAPI(
        title="StadiumMind AI",
        version="0.1.0",
        description="GenAI operating system for FIFA World Cup 2026 stadiums.",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # demo; restrict in production
        allow_methods=["*"],
        allow_headers=["*"],
    )
    # Expose the service so tests / other code can reach it via app.state.
    app.state.service = service

    # ------------------------------------------------------------------ #
    # Auth dependency
    # ------------------------------------------------------------------ #
    def require_role(*allowed: str):
        """Return a dependency enforcing that the caller holds an allowed role."""

        def _dependency(authorization: str | None = Header(default=None)) -> dict:
            if not authorization or not authorization.lower().startswith("bearer "):
                raise HTTPException(status_code=401, detail="missing bearer token")
            token = authorization.split(" ", 1)[1]
            try:
                payload = verify_token(settings, token)
            except AuthError as exc:
                raise HTTPException(status_code=401, detail=str(exc)) from exc
            if allowed and payload.get("role") not in allowed:
                raise HTTPException(status_code=403, detail="insufficient role")
            return payload

        return _dependency

    # ------------------------------------------------------------------ #
    # Meta
    # ------------------------------------------------------------------ #
    @app.get("/api/health")
    def health() -> dict:
        return {
            "status": "ok",
            "match_minute": service.match_minute,
            "llm": service.orchestrator.llm.name,
            "predictor_backend": service.orchestrator.predictor.backend,
            "match_source": service.match_provider.name,
            "directions_provider": service.directions_provider.name,
            "maps_enabled": service.maps_enabled,
            "venue": service.venue.anchor.name,
        }

    @app.post("/api/auth/login", response_model=TokenResponse)
    def login(req: LoginRequest) -> TokenResponse:
        try:
            token = issue_token(settings, req.username, req.role)
        except AuthError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return TokenResponse(access_token=token, role=req.role)

    # ------------------------------------------------------------------ #
    # Venue & crowd
    # ------------------------------------------------------------------ #
    @app.get("/api/venue")
    def venue() -> dict:
        v = service.venue
        return {
            "anchor": {
                "name": v.anchor.name,
                "lat": v.anchor.lat,
                "lng": v.anchor.lng,
                "footprint_m": v.anchor.footprint_m,
            },
            "zones": [
                {
                    "id": z.id,
                    "name": z.name,
                    "type": z.type.value,
                    "x": z.x,
                    "y": z.y,
                    "lat": z.lat,
                    "lng": z.lng,
                    "capacity": z.capacity,
                    "neighbours": z.neighbours,
                    "accessible": z.accessible,
                }
                for z in v
            ],
        }

    @app.get("/api/match", response_model=MatchOut)
    def match() -> MatchOut:
        return MatchOut.from_domain(service.match())

    @app.get("/api/directions", response_model=DirectionsOut)
    def directions(origin: str, destination: str) -> DirectionsOut:
        try:
            result = service.directions(origin, destination)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return DirectionsOut(
            origin=origin,
            destination=destination,
            distance_m=result.distance_m,
            duration_min=result.duration_min,
            provider=result.provider,
            polyline=[[lat, lng] for lat, lng in result.polyline],
            steps=result.steps,
        )

    @app.get("/api/crowd/heatmap", response_model=list[ZoneHeat])
    def heatmap() -> list[ZoneHeat]:
        return [ZoneHeat(**z) for z in service.heatmap()]

    @app.post("/api/crowd/tick", response_model=list[ZoneHeat])
    def tick() -> list[ZoneHeat]:
        service.tick()
        return [ZoneHeat(**z) for z in service.heatmap()]

    @app.post("/api/crowd/surge")
    def surge(zone_id: str, people: int = 3000) -> dict:
        try:
            service.inject_surge(zone_id, people)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return {"status": "queued", "zone_id": zone_id, "people": people}

    @app.get("/api/alerts", response_model=list[AlertOut])
    def alerts() -> list[AlertOut]:
        return [
            AlertOut(id=a.id, message=a.message, zone_id=a.zone_id, level=a.level.value)
            for a in service.alerts()
        ]

    # ------------------------------------------------------------------ #
    # AI
    # ------------------------------------------------------------------ #
    @app.get("/api/ai/recommendations", response_model=list[RecommendationOut])
    def recommendations() -> list[RecommendationOut]:
        return [RecommendationOut.from_domain(r) for r in service.recommendations()]

    @app.get("/api/ai/intents")
    def intents() -> dict:
        return {"intents": service.supported_intents()}

    @app.post("/api/ai/query", response_model=RecommendationOut)
    def query(req: QueryRequest) -> RecommendationOut:
        result = service.ask(req.intent, req.params)
        if result is None:
            raise HTTPException(
                status_code=404, detail=f"no answer for intent {req.intent!r}"
            )
        return RecommendationOut.from_domain(result)

    @app.post(
        "/api/ai/recommendations/{rec_id}/decision",
        response_model=RecommendationOut,
    )
    def decide(
        rec_id: str,
        req: DecisionRequest,
        _user: dict = Depends(require_role("operations", "security")),
    ) -> RecommendationOut:
        result = service.decide(rec_id, req.approved)
        if result is None:
            raise HTTPException(status_code=404, detail="recommendation not found")
        return RecommendationOut.from_domain(result)

    # ------------------------------------------------------------------ #
    # Incidents
    # ------------------------------------------------------------------ #
    @app.post("/api/incidents", response_model=IncidentOut)
    def report_incident(
        req: IncidentRequest,
        _user: dict = Depends(require_role("operations", "security", "medical")),
    ) -> IncidentOut:
        try:
            inc = service.report_incident(
                req.type, req.severity, req.zone_id, req.description
            )
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return IncidentOut.from_domain(inc)

    @app.get("/api/incidents", response_model=list[IncidentOut])
    def list_incidents(include_resolved: bool = True) -> list[IncidentOut]:
        return [
            IncidentOut.from_domain(i)
            for i in service.list_incidents(include_resolved)
        ]

    @app.post("/api/incidents/{incident_id}/resolve", response_model=IncidentOut)
    def resolve_incident(
        incident_id: str,
        _user: dict = Depends(require_role("operations", "security", "medical")),
    ) -> IncidentOut:
        inc = service.resolve_incident(incident_id)
        if inc is None:
            raise HTTPException(status_code=404, detail="incident not found")
        return IncidentOut.from_domain(inc)

    # ------------------------------------------------------------------ #
    # WebSocket live feed
    # ------------------------------------------------------------------ #
    @app.websocket("/ws/live")
    async def live(ws: WebSocket) -> None:
        """Stream heatmap + recommendation updates once per interval."""
        await ws.accept()
        try:
            while True:
                service.tick()
                await ws.send_json(
                    {
                        "match_minute": service.match_minute,
                        "heatmap": service.heatmap(),
                        "recommendations": [
                            RecommendationOut.from_domain(r).model_dump()
                            for r in service.recommendations()
                        ],
                    }
                )
                await asyncio.sleep(settings.simulation_tick_seconds)
        except WebSocketDisconnect:  # pragma: no cover - network event
            logger.info("live client disconnected")

    return app
