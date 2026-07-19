"""Key/value cache abstraction.

Used for hot state such as the latest crowd snapshot. Production uses Redis;
the fallback is an in-process dict with optional TTL. Values are JSON encoded
so both backends behave identically.
"""

from __future__ import annotations

import json
import logging
import threading
import time
from abc import ABC, abstractmethod
from typing import Any

from stadiummind.core.config import Settings

logger = logging.getLogger(__name__)


class KeyValueStore(ABC):
    """Abstract JSON key/value store with optional per-key TTL."""

    @abstractmethod
    def set(self, key: str, value: Any, ttl_seconds: float | None = None) -> None:
        ...

    @abstractmethod
    def get(self, key: str) -> Any | None:
        ...

    @abstractmethod
    def delete(self, key: str) -> None:
        ...


class InMemoryStore(KeyValueStore):
    """Thread-safe dict-backed store with lazy TTL expiry."""

    def __init__(self) -> None:
        # key -> (json_value, expires_at | None)
        self._data: dict[str, tuple[str, float | None]] = {}
        self._lock = threading.RLock()

    def set(self, key: str, value: Any, ttl_seconds: float | None = None) -> None:
        expires_at = time.time() + ttl_seconds if ttl_seconds else None
        with self._lock:
            self._data[key] = (json.dumps(value), expires_at)

    def get(self, key: str) -> Any | None:
        with self._lock:
            entry = self._data.get(key)
            if entry is None:
                return None
            payload, expires_at = entry
            if expires_at is not None and time.time() > expires_at:
                del self._data[key]
                return None
            return json.loads(payload)

    def delete(self, key: str) -> None:
        with self._lock:
            self._data.pop(key, None)


class RedisStore(KeyValueStore):  # pragma: no cover - requires a live server
    """Redis-backed store, used only when redis-py is installed and configured."""

    def __init__(self, url: str) -> None:
        import redis  # local import: optional dependency

        self._client = redis.Redis.from_url(url, decode_responses=True)

    def set(self, key: str, value: Any, ttl_seconds: float | None = None) -> None:
        payload = json.dumps(value)
        if ttl_seconds:
            self._client.setex(key, int(ttl_seconds), payload)
        else:
            self._client.set(key, payload)

    def get(self, key: str) -> Any | None:
        payload = self._client.get(key)
        return json.loads(payload) if payload is not None else None

    def delete(self, key: str) -> None:
        self._client.delete(key)


def build_key_value_store(settings: Settings) -> KeyValueStore:
    """Return a Redis store when configured/available, else in-memory."""
    if settings.redis_url:
        try:
            store = RedisStore(settings.redis_url)
            store.set("__ping__", 1, ttl_seconds=5)  # fail fast if unreachable
            return store
        except Exception:  # noqa: BLE001
            logger.warning("Redis unavailable; falling back to in-memory store")
    return InMemoryStore()
