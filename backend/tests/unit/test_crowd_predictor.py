"""Unit tests for the crowd predictor (backend-agnostic behaviour)."""

from stadiummind.ml.crowd_predictor import CrowdPredictor


def test_predictor_builds_with_some_backend():
    p = CrowdPredictor()
    assert p.backend in {"xgboost", "lightgbm", "linear-fallback"}


def test_prediction_is_bounded():
    p = CrowdPredictor()
    ratio = p.predict_ratio(0.5, arrival_rate_per_min=20, match_minute=30)
    assert 0.0 <= ratio <= 1.2


def test_more_arrivals_predicts_higher_or_equal_occupancy():
    p = CrowdPredictor()
    low = p.predict_ratio(0.5, arrival_rate_per_min=1, match_minute=30)
    high = p.predict_ratio(0.5, arrival_rate_per_min=45, match_minute=30)
    assert high >= low


def test_minutes_to_congestion_none_when_empty():
    p = CrowdPredictor()
    # An empty, low-arrival zone should not congest within the horizon.
    result = p.predict_minutes_to_congestion(
        current_ratio=0.05, arrival_rate_per_min=0.5, match_minute=10, threshold=0.9
    )
    assert result is None


def test_minutes_to_congestion_triggers_when_busy():
    p = CrowdPredictor()
    result = p.predict_minutes_to_congestion(
        current_ratio=0.85, arrival_rate_per_min=45, match_minute=40, threshold=0.9
    )
    assert result is not None and result >= 1
