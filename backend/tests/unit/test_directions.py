"""Unit tests for directions providers (HTTP mocked)."""

import httpx
import pytest

from stadiummind.core.config import Settings
from stadiummind.integrations.directions import (
    GoogleDirectionsProvider,
    HaversineDirections,
    build_directions_provider,
    decode_polyline,
    haversine_m,
)


def test_haversine_known_distance():
    # ~1 degree of latitude is ~111 km.
    d = haversine_m((0.0, 0.0), (1.0, 0.0))
    assert 110_000 < d < 112_000


def test_decode_polyline_reference_example():
    # The canonical example from Google's polyline algorithm docs.
    points = decode_polyline("_p~iF~ps|U_ulLnnqC_mqNvxq`@")
    assert points[0] == pytest.approx((38.5, -120.2), abs=1e-3)
    assert len(points) == 3


def test_haversine_provider_walking():
    result = HaversineDirections().walking((40.8135, -74.0742), (40.8149, -74.0773))
    assert result.provider == "haversine"
    assert result.distance_m > 0 and result.duration_min > 0
    assert len(result.polyline) == 2


def test_build_defaults_to_haversine_without_key():
    assert build_directions_provider(Settings(google_maps_api_key=None)).name == "haversine"


def test_build_selects_google_with_key():
    assert build_directions_provider(Settings(google_maps_api_key="k")).name == "google"


class _FakeResp:
    def __init__(self, payload):
        self._p = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._p


class _FakeClient:
    payload: dict = {}

    def __init__(self, *a, **k):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def get(self, url, params=None):
        return _FakeResp(_FakeClient.payload)


def test_google_directions_parsed(monkeypatch):
    _FakeClient.payload = {
        "status": "OK",
        "routes": [
            {
                "overview_polyline": {"points": "_p~iF~ps|U_ulLnnqC_mqNvxq`@"},
                "legs": [
                    {
                        "distance": {"value": 640},
                        "duration": {"value": 480},
                        "steps": [{"html_instructions": "Walk <b>north</b>"}],
                    }
                ],
            }
        ],
    }
    monkeypatch.setattr(httpx, "Client", _FakeClient)
    result = GoogleDirectionsProvider(api_key="k").walking((40.81, -74.07), (40.82, -74.08))
    assert result.provider == "google"
    assert result.distance_m == 640
    assert result.duration_min == 8.0
    assert result.steps == ["Walk north"]


def test_google_directions_falls_back_when_not_ok(monkeypatch):
    _FakeClient.payload = {"status": "ZERO_RESULTS", "routes": []}
    monkeypatch.setattr(httpx, "Client", _FakeClient)
    result = GoogleDirectionsProvider(api_key="k").walking((40.81, -74.07), (40.82, -74.08))
    # Falls back to the haversine estimate rather than raising.
    assert result.provider == "haversine"
