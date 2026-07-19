"""Short-horizon crowd forecasting.

Predicts the occupancy ratio of a zone a few minutes into the future from a
small feature vector (current ratio, arrival rate, minute-of-match, recent
trend). The heavy gradient-boosting libraries are *optional*:

* If ``xgboost`` (preferred) or ``lightgbm`` is installed, a real regressor is
  trained on synthetic-but-plausible data at construction time.
* Otherwise the class transparently falls back to a closed-form linear model.

Either way the public interface — :meth:`predict_ratio` and
:meth:`predict_minutes_to_congestion` — is identical, so the agents don't care
which backend is active. ``backend`` reports the choice for observability.
"""

from __future__ import annotations

import logging

import numpy as np

logger = logging.getLogger(__name__)

# Number of synthetic rows used to fit the model.
_TRAIN_ROWS = 4000
# Feature layout: [current_ratio, arrival_rate_norm, minute_norm, trend].
_N_FEATURES = 4


def _generate_training_data(seed: int = 7) -> tuple[np.ndarray, np.ndarray]:
    """Create a synthetic dataset linking features to future occupancy ratio.

    The generating function is intentionally non-linear (products and a
    saturating term) so that a gradient-boosted model can add value over the
    linear fallback, while remaining physically sensible: more arrivals and an
    upward trend push future occupancy higher.
    """
    rng = np.random.default_rng(seed)
    current = rng.uniform(0.0, 1.0, _TRAIN_ROWS)
    arrivals = rng.uniform(0.0, 1.0, _TRAIN_ROWS)
    minute = rng.uniform(0.0, 1.0, _TRAIN_ROWS)
    trend = rng.uniform(-0.2, 0.2, _TRAIN_ROWS)

    future = (
        current
        + 0.6 * arrivals * (1.0 - current)  # arrivals fill remaining space
        + 0.8 * trend  # momentum
        + 0.1 * arrivals * minute  # busier near kickoff
    )
    future = np.clip(future + rng.normal(0, 0.03, _TRAIN_ROWS), 0.0, 1.2)

    X = np.column_stack([current, arrivals, minute, trend])
    return X, future


class _LinearFallback:
    """Ordinary-least-squares model used when no GBM library is available."""

    def __init__(self) -> None:
        X, y = _generate_training_data()
        # Add bias column and solve the normal equations.
        A = np.column_stack([np.ones(len(X)), X])
        self._coef, *_ = np.linalg.lstsq(A, y, rcond=None)

    def predict(self, X: np.ndarray) -> np.ndarray:
        A = np.column_stack([np.ones(len(X)), X])
        return A @ self._coef


class CrowdPredictor:
    """Predicts near-future congestion for a zone."""

    def __init__(self, prefer: str = "xgboost") -> None:
        self._model, self.backend = self._build_model(prefer)

    # -- construction -----------------------------------------------------
    @staticmethod
    def _build_model(prefer: str):
        """Try GBM libraries in order, else fall back to linear regression."""
        order = [prefer] + [b for b in ("xgboost", "lightgbm") if b != prefer]
        X, y = _generate_training_data()
        for backend in order:
            try:
                if backend == "xgboost":
                    import xgboost as xgb  # optional dependency

                    model = xgb.XGBRegressor(
                        n_estimators=120,
                        max_depth=4,
                        learning_rate=0.1,
                        verbosity=0,
                    )
                    model.fit(X, y)
                    return model, "xgboost"
                if backend == "lightgbm":
                    import lightgbm as lgb  # optional dependency

                    model = lgb.LGBMRegressor(
                        n_estimators=120, max_depth=4, learning_rate=0.1
                    )
                    model.fit(X, y)
                    return model, "lightgbm"
            except Exception:  # noqa: BLE001 - library missing or failed to fit
                logger.info("crowd predictor: %s unavailable", backend)
        return _LinearFallback(), "linear-fallback"

    # -- prediction -------------------------------------------------------
    def predict_ratio(
        self,
        current_ratio: float,
        arrival_rate_per_min: float,
        match_minute: int,
        trend: float = 0.0,
    ) -> float:
        """Predict the occupancy ratio a few minutes ahead (clamped 0-1.2)."""
        features = np.array(
            [
                [
                    _clip01(current_ratio),
                    _clip01(arrival_rate_per_min / 50.0),  # normalise ~[0,1]
                    _clip01(match_minute / 120.0),
                    float(np.clip(trend, -1.0, 1.0)),
                ]
            ],
            dtype=float,
        )
        prediction = float(self._model.predict(features)[0])
        return float(np.clip(prediction, 0.0, 1.2))

    def predict_minutes_to_congestion(
        self,
        current_ratio: float,
        arrival_rate_per_min: float,
        match_minute: int,
        threshold: float = 0.9,
        horizon: int = 20,
    ) -> int | None:
        """Estimate minutes until a zone crosses ``threshold`` occupancy.

        Iteratively rolls the predictor forward one minute at a time. Returns
        ``None`` if congestion is not reached within ``horizon`` minutes.
        """
        ratio = current_ratio
        for minute_ahead in range(1, horizon + 1):
            next_ratio = self.predict_ratio(
                ratio,
                arrival_rate_per_min,
                match_minute + minute_ahead,
                trend=next_ratio_trend(ratio),
            )
            if next_ratio >= threshold:
                return minute_ahead
            ratio = next_ratio
        return None


def next_ratio_trend(ratio: float) -> float:
    """Simple momentum proxy: mild positive trend below saturation."""
    return 0.05 if ratio < 0.9 else 0.0


def _clip01(value: float) -> float:
    return float(np.clip(value, 0.0, 1.0))
