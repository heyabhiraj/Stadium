"""Match-data providers.

Real data comes from **football-data.org** (v4 REST API, free-tier token in the
``X-Auth-Token`` header). When no token is configured, a deterministic
:class:`MockMatchProvider` returns the demo fixture so the UI and tests work
offline.

All HTTP happens through ``httpx`` and is wrapped so a network/API failure
degrades to the mock rather than crashing the request.
"""

from __future__ import annotations

import logging

from stadiummind.core.config import Settings, get_settings
from stadiummind.core.models import Match

logger = logging.getLogger(__name__)

_FOOTBALL_DATA_BASE = "https://api.football-data.org/v4"


class MatchProvider:
    """Abstract source of the current match."""

    name = "abstract"

    def current_match(self) -> Match:  # pragma: no cover - abstract
        raise NotImplementedError


class MockMatchProvider(MatchProvider):
    """Deterministic offline fixture (Brazil vs Spain at MetLife)."""

    name = "mock"

    def __init__(self, venue_name: str = "MetLife Stadium") -> None:
        self._venue = venue_name

    def current_match(self) -> Match:
        return Match(
            id="mock-1",
            home_team="Brazil",
            away_team="Spain",
            competition="FIFA World Cup 2026",
            venue=self._venue,
            kickoff_utc="2026-07-19T19:30:00Z",
            status="SCHEDULED",
            source="mock",
        )


class FootballDataProvider(MatchProvider):
    """Live match data from football-data.org."""

    name = "football-data"

    def __init__(
        self,
        api_key: str,
        competition: str = "WC",
        match_id: str | None = None,
        venue_name: str = "MetLife Stadium",
        timeout: float = 8.0,
    ) -> None:
        self._api_key = api_key
        self._competition = competition
        self._match_id = match_id
        self._venue = venue_name
        self._timeout = timeout

    # -- public -----------------------------------------------------------
    def current_match(self) -> Match:
        """Return a pinned match, else the next/live match in the competition.

        Any failure (missing dependency, network error, empty result) falls
        back to the deterministic mock so the caller always gets a Match.
        """
        try:
            payload = self._fetch()
            return self._parse(payload)
        except Exception as exc:  # noqa: BLE001
            logger.warning("football-data fetch failed (%s); using mock", exc)
            return MockMatchProvider(self._venue).current_match()

    # -- internals --------------------------------------------------------
    def _fetch(self) -> dict:
        import httpx  # httpx is a core dependency (FastAPI TestClient uses it)

        headers = {"X-Auth-Token": self._api_key}
        with httpx.Client(timeout=self._timeout, headers=headers) as client:
            if self._match_id:
                resp = client.get(f"{_FOOTBALL_DATA_BASE}/matches/{self._match_id}")
                resp.raise_for_status()
                return resp.json()
            # Otherwise take the earliest scheduled/live match in the competition.
            resp = client.get(
                f"{_FOOTBALL_DATA_BASE}/competitions/{self._competition}/matches"
            )
            resp.raise_for_status()
            return resp.json()

    def _parse(self, payload: dict) -> Match:
        """Map football-data.org JSON onto our normalised :class:`Match`.

        Handles both response shapes: the competition-matches list
        (``{"matches": [...]}``) and the single-match endpoint, which returns
        the match object at the top level.
        """
        if "matches" in payload:
            match = self._pick_match(payload["matches"])
        elif "match" in payload:
            match = payload["match"]
        elif payload.get("homeTeam") or payload.get("id"):
            match = payload  # single-match endpoint, top-level object
        else:
            match = None
        if not match:
            raise ValueError("no match in response")

        score = match.get("score", {}).get("fullTime", {})
        return Match(
            id=str(match.get("id", "")),
            home_team=(match.get("homeTeam") or {}).get("name", "Home"),
            away_team=(match.get("awayTeam") or {}).get("name", "Away"),
            competition=(match.get("competition") or {}).get("name", self._competition),
            venue=match.get("venue") or self._venue,
            kickoff_utc=match.get("utcDate"),
            status=match.get("status", "SCHEDULED"),
            home_score=score.get("home"),
            away_score=score.get("away"),
            minute=match.get("minute"),
            source="football-data",
        )

    @staticmethod
    def _pick_match(matches: list[dict]) -> dict | None:
        """Prefer a live match, else the earliest scheduled one."""
        if not matches:
            return None
        live = [m for m in matches if m.get("status") in {"LIVE", "IN_PLAY", "PAUSED"}]
        if live:
            return live[0]
        scheduled = [m for m in matches if m.get("status") in {"SCHEDULED", "TIMED"}]
        pool = scheduled or matches
        return sorted(pool, key=lambda m: m.get("utcDate") or "")[0]


def build_match_provider(settings: Settings | None = None) -> MatchProvider:
    """Factory: football-data.org when a key is set, else the mock."""
    settings = settings or get_settings()
    if settings.football_data_api_key:
        return FootballDataProvider(
            api_key=settings.football_data_api_key,
            competition=settings.football_data_competition,
            match_id=settings.football_data_match_id,
            timeout=settings.external_timeout_seconds,
        )
    return MockMatchProvider()
