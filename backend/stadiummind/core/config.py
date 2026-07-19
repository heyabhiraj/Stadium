"""Central application configuration.

Configuration is read once from the environment and cached. Keeping every
tunable in a single typed object (rather than scattering ``os.getenv`` calls
across the codebase) makes the system easy to reason about and to test: a test
can build its own :class:`Settings` and inject it anywhere.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from functools import lru_cache


@dataclass(frozen=True)
class Settings:
    """Immutable, typed application settings.

    Attributes are populated from environment variables by
    :meth:`from_env`, but the dataclass can also be instantiated directly in
    tests to override any value.
    """

    # --- LLM -------------------------------------------------------------
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-1.5-flash"
    llm_timeout_seconds: float = 20.0
    # When True, the system uses the deterministic MockLLM even if a key is set.
    force_mock_llm: bool = False

    # --- Infrastructure endpoints (optional) -----------------------------
    database_url: str | None = None          # e.g. postgresql+psycopg://...
    redis_url: str | None = None             # e.g. redis://localhost:6379/0
    kafka_bootstrap_servers: str | None = None

    # --- External APIs (optional) ----------------------------------------
    # Google Maps: the JS API key is used by the frontend; the same key (or a
    # server-restricted one) is used here for the Directions API.
    google_maps_api_key: str | None = None
    # football-data.org: free-tier token + which match to show.
    football_data_api_key: str | None = None
    football_data_competition: str = "WC"    # FIFA World Cup competition code
    football_data_match_id: str | None = None  # pin a specific match if desired
    external_timeout_seconds: float = 8.0

    # --- Simulation ------------------------------------------------------
    simulation_seed: int = 42
    simulation_tick_seconds: float = 1.0

    # --- Domain thresholds ----------------------------------------------
    # Occupancy ratio (0-1) above which a zone is considered "congested".
    congestion_threshold: float = 0.80
    # Predicted wait (minutes) above which the crowd agent raises an alert.
    queue_alert_minutes: float = 15.0

    # --- Auth (demo-grade) ----------------------------------------------
    jwt_secret: str = "dev-secret-change-me"
    access_token_ttl_minutes: int = 720

    # Roles recognised by the auth layer.
    roles: tuple[str, ...] = field(
        default=("fan", "volunteer", "operations", "security", "medical")
    )

    @classmethod
    def from_env(cls) -> "Settings":
        """Build settings from environment variables with safe defaults."""

        def _flag(name: str, default: bool = False) -> bool:
            raw = os.getenv(name)
            if raw is None:
                return default
            return raw.strip().lower() in {"1", "true", "yes", "on"}

        def _float(name: str, default: float) -> float:
            raw = os.getenv(name)
            try:
                return float(raw) if raw is not None else default
            except ValueError:
                return default

        return cls(
            gemini_api_key=os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"),
            gemini_model=os.getenv("GEMINI_MODEL", "gemini-1.5-flash"),
            llm_timeout_seconds=_float("LLM_TIMEOUT_SECONDS", 20.0),
            force_mock_llm=_flag("FORCE_MOCK_LLM", False),
            database_url=os.getenv("DATABASE_URL"),
            redis_url=os.getenv("REDIS_URL"),
            kafka_bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP_SERVERS"),
            google_maps_api_key=os.getenv("GOOGLE_MAPS_API_KEY"),
            football_data_api_key=os.getenv("FOOTBALL_DATA_API_KEY"),
            football_data_competition=os.getenv("FOOTBALL_DATA_COMPETITION", "WC"),
            football_data_match_id=os.getenv("FOOTBALL_DATA_MATCH_ID"),
            external_timeout_seconds=_float("EXTERNAL_TIMEOUT_SECONDS", 8.0),
            simulation_seed=int(os.getenv("SIMULATION_SEED", "42")),
            simulation_tick_seconds=_float("SIMULATION_TICK_SECONDS", 1.0),
            congestion_threshold=_float("CONGESTION_THRESHOLD", 0.80),
            queue_alert_minutes=_float("QUEUE_ALERT_MINUTES", 15.0),
            jwt_secret=os.getenv("JWT_SECRET", "dev-secret-change-me"),
            access_token_ttl_minutes=int(os.getenv("ACCESS_TOKEN_TTL_MINUTES", "720")),
        )

    @property
    def gemini_enabled(self) -> bool:
        """True when a real Gemini call should be attempted."""
        return bool(self.gemini_api_key) and not self.force_mock_llm


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the process-wide cached settings instance."""
    return Settings.from_env()
