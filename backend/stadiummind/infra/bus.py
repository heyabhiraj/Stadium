"""Message bus abstraction (publish/subscribe).

The stadium is an event-driven system: crowd readings, incidents and
recommendations all flow as events. In production these travel over Kafka; in
development and tests they travel over a thread-safe in-process bus. Both share
the :class:`MessageBus` interface so producers/consumers never change.
"""

from __future__ import annotations

import json
import logging
import threading
from abc import ABC, abstractmethod
from collections import defaultdict
from typing import Callable

from stadiummind.core.config import Settings

logger = logging.getLogger(__name__)

# A subscriber receives the decoded JSON payload of a message.
Subscriber = Callable[[dict], None]


class MessageBus(ABC):
    """Abstract publish/subscribe message bus."""

    @abstractmethod
    def publish(self, topic: str, message: dict) -> None:
        """Publish ``message`` (a JSON-serialisable dict) to ``topic``."""

    @abstractmethod
    def subscribe(self, topic: str, handler: Subscriber) -> None:
        """Register ``handler`` to be called for every message on ``topic``."""

    def close(self) -> None:  # pragma: no cover - default no-op
        """Release any resources held by the bus."""


class InMemoryBus(MessageBus):
    """Thread-safe, synchronous in-process bus.

    ``publish`` invokes each subscriber immediately on the calling thread. A
    lock guards the subscriber registry so it is safe to use from FastAPI's
    threadpool and background tasks.
    """

    def __init__(self) -> None:
        self._subscribers: dict[str, list[Subscriber]] = defaultdict(list)
        self._lock = threading.RLock()

    def publish(self, topic: str, message: dict) -> None:
        with self._lock:
            handlers = list(self._subscribers.get(topic, ()))
        for handler in handlers:
            try:
                handler(message)
            except Exception:  # noqa: BLE001 - one bad subscriber must not break others
                logger.exception("subscriber for topic %s raised", topic)

    def subscribe(self, topic: str, handler: Subscriber) -> None:
        with self._lock:
            self._subscribers[topic].append(handler)


class KafkaBus(MessageBus):  # pragma: no cover - requires a live broker
    """Kafka-backed bus. Instantiated only when kafka-python is installed and
    ``KAFKA_BOOTSTRAP_SERVERS`` is configured."""

    def __init__(self, bootstrap_servers: str) -> None:
        from kafka import KafkaProducer  # local import: optional dependency

        self._bootstrap = bootstrap_servers
        self._producer = KafkaProducer(
            bootstrap_servers=bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        )
        self._consumer_threads: list[threading.Thread] = []

    def publish(self, topic: str, message: dict) -> None:
        self._producer.send(topic, message)

    def subscribe(self, topic: str, handler: Subscriber) -> None:
        from kafka import KafkaConsumer

        def _run() -> None:
            consumer = KafkaConsumer(
                topic,
                bootstrap_servers=self._bootstrap,
                value_deserializer=lambda m: json.loads(m.decode("utf-8")),
                auto_offset_reset="latest",
            )
            for record in consumer:
                try:
                    handler(record.value)
                except Exception:  # noqa: BLE001
                    logger.exception("kafka subscriber for %s raised", topic)

        thread = threading.Thread(target=_run, daemon=True)
        thread.start()
        self._consumer_threads.append(thread)

    def close(self) -> None:
        self._producer.flush()
        self._producer.close()


def build_message_bus(settings: Settings) -> MessageBus:
    """Return a Kafka bus when configured/available, else the in-memory bus."""
    if settings.kafka_bootstrap_servers:
        try:
            return KafkaBus(settings.kafka_bootstrap_servers)
        except Exception:  # noqa: BLE001 - kafka missing or unreachable
            logger.warning("Kafka unavailable; falling back to in-memory bus")
    return InMemoryBus()
