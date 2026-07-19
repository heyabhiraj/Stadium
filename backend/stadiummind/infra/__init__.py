"""Infrastructure layer: streaming, caching and persistence.

Each concern is expressed as an abstract interface with two implementations:
a production integration (Kafka / Redis / SQL) and an in-process fallback used
for local development and testing. A factory function picks the right one from
:class:`~stadiummind.core.config.Settings`, so the rest of the application only
ever depends on the interface.
"""

from stadiummind.infra.bus import InMemoryBus, MessageBus, build_message_bus
from stadiummind.infra.cache import (
    InMemoryStore,
    KeyValueStore,
    build_key_value_store,
)
from stadiummind.infra.repository import (
    InMemoryRepository,
    Repository,
    build_repository,
)

__all__ = [
    "MessageBus",
    "InMemoryBus",
    "build_message_bus",
    "KeyValueStore",
    "InMemoryStore",
    "build_key_value_store",
    "Repository",
    "InMemoryRepository",
    "build_repository",
]
