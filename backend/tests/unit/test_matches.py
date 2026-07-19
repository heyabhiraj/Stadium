"""Unit tests for match-data providers (HTTP mocked)."""

import httpx
import pytest

from stadiummind.core.config import Settings
from stadiummind.integrations.matches import (
    FootballDataProvider,
    MockMatchProvider,
    build_match_provider,
)


class _FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


class _FakeClient:
    """Stand-in for httpx.Client that returns a canned payload."""

    payload: dict = {}

    def __init__(self, *args, **kwargs):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def get(self, url, params=None):
        return _FakeResponse(_FakeClient.payload)


def test_mock_provider_is_deterministic():
    m1 = MockMatchProvider().current_match()
    m2 = MockMatchProvider().current_match()
    assert m1.home_team == "Brazil" and m1.away_team == "Spain"
    assert m1.source == "mock"
    assert m1 == m2


def test_build_defaults_to_mock_without_key():
    assert build_match_provider(Settings(football_data_api_key=None)).name == "mock"


def test_build_selects_football_data_with_key():
    provider = build_match_provider(Settings(football_data_api_key="tok"))
    assert provider.name == "football-data"


def test_football_data_parses_competition_matches(monkeypatch):
    _FakeClient.payload = {
        "matches": [
            {
                "id": 111,
                "status": "IN_PLAY",
                "utcDate": "2026-07-19T19:30:00Z",
                "minute": 57,
                "homeTeam": {"name": "Argentina"},
                "awayTeam": {"name": "France"},
                "competition": {"name": "FIFA World Cup"},
                "score": {"fullTime": {"home": 2, "away": 1}},
            }
        ]
    }
    monkeypatch.setattr(httpx, "Client", _FakeClient)
    provider = FootballDataProvider(api_key="tok")
    match = provider.current_match()
    assert match.source == "football-data"
    assert match.home_team == "Argentina" and match.away_team == "France"
    assert match.status == "IN_PLAY" and match.home_score == 2 and match.minute == 57


def test_football_data_falls_back_on_error(monkeypatch):
    class _Boom(_FakeClient):
        def get(self, url, params=None):
            raise RuntimeError("network down")

    monkeypatch.setattr(httpx, "Client", _Boom)
    match = FootballDataProvider(api_key="tok").current_match()
    # Graceful degradation to the deterministic mock.
    assert match.source == "mock"


def test_football_data_parses_single_match_endpoint(monkeypatch):
    # GET /matches/{id} returns the match object at the top level.
    _FakeClient.payload = {
        "id": 222,
        "status": "SCHEDULED",
        "utcDate": "2026-07-19T19:30:00Z",
        "homeTeam": {"name": "Brazil"},
        "awayTeam": {"name": "Spain"},
        "competition": {"name": "FIFA World Cup"},
        "score": {"fullTime": {"home": None, "away": None}},
    }
    monkeypatch.setattr(httpx, "Client", _FakeClient)
    provider = FootballDataProvider(api_key="tok", match_id="222")
    match = provider.current_match()
    assert match.source == "football-data"
    assert match.home_team == "Brazil" and match.id == "222"


def test_pick_match_prefers_live():
    matches = [
        {"status": "SCHEDULED", "utcDate": "2026-07-10T00:00:00Z"},
        {"status": "IN_PLAY", "utcDate": "2026-07-19T19:30:00Z"},
    ]
    chosen = FootballDataProvider._pick_match(matches)
    assert chosen["status"] == "IN_PLAY"
