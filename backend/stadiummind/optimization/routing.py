"""Walking-route search over the venue graph.

Provides both a shortest-distance route and a congestion-aware route that
penalises busy zones (used by the "Avoid Crowd" toggle in the Fan app). The
search is Dijkstra over the venue's undirected graph with edge weights derived
from Euclidean distance plus an optional congestion penalty.
"""

from __future__ import annotations

import heapq

from stadiummind.core.models import CrowdReading, Route
from stadiummind.core.venue import Venue

# Assumed average walking speed, metres per minute (~5 km/h).
_WALK_SPEED_M_PER_MIN = 80.0


class RouteOptimizer:
    """Computes routes between zones, optionally avoiding congestion."""

    def __init__(self, venue: Venue) -> None:
        self.venue = venue

    def route(
        self,
        origin: str,
        destination: str,
        crowd: dict[str, CrowdReading] | None = None,
        avoid_congestion: bool = False,
        accessible_only: bool = False,
    ) -> Route:
        """Return the best :class:`Route` from ``origin`` to ``destination``.

        When ``avoid_congestion`` is set and a ``crowd`` snapshot is supplied,
        edge costs are inflated in proportion to the destination zone's
        occupancy ratio, steering the path away from red zones.
        """
        if origin not in self.venue or destination not in self.venue:
            raise KeyError("origin/destination must be known zones")

        dist, prev = self._dijkstra(
            origin, destination, crowd, avoid_congestion, accessible_only
        )
        if destination not in prev and origin != destination:
            raise ValueError("no route found under the given constraints")

        path = self._reconstruct(prev, origin, destination)
        distance_m = self._path_distance(path)
        eta = distance_m / _WALK_SPEED_M_PER_MIN
        return Route(
            origin=origin,
            destination=destination,
            path=path,
            distance_m=round(distance_m, 1),
            eta_minutes=round(eta, 1),
            avoids_congestion=avoid_congestion,
            accessible=all(self.venue.get(z).accessible for z in path),
        )

    # ------------------------------------------------------------------ #
    # Internals
    # ------------------------------------------------------------------ #
    def _edge_cost(
        self,
        a: str,
        b: str,
        crowd: dict[str, CrowdReading] | None,
        avoid_congestion: bool,
    ) -> float:
        cost = self.venue.distance(a, b)
        if avoid_congestion and crowd and b in crowd:
            # Multiply cost by up to 4x as the target zone approaches capacity.
            cost *= 1.0 + 3.0 * min(crowd[b].ratio, 1.0)
        return cost

    def _dijkstra(
        self,
        origin: str,
        destination: str,
        crowd: dict[str, CrowdReading] | None,
        avoid_congestion: bool,
        accessible_only: bool,
    ) -> tuple[dict[str, float], dict[str, str]]:
        dist: dict[str, float] = {origin: 0.0}
        prev: dict[str, str] = {}
        pq: list[tuple[float, str]] = [(0.0, origin)]
        visited: set[str] = set()

        while pq:
            d, node = heapq.heappop(pq)
            if node in visited:
                continue
            visited.add(node)
            if node == destination:
                break
            for neighbour in self.venue.get(node).neighbours:
                if accessible_only and not self.venue.get(neighbour).accessible:
                    continue
                new_cost = d + self._edge_cost(node, neighbour, crowd, avoid_congestion)
                if new_cost < dist.get(neighbour, float("inf")):
                    dist[neighbour] = new_cost
                    prev[neighbour] = node
                    heapq.heappush(pq, (new_cost, neighbour))
        return dist, prev

    @staticmethod
    def _reconstruct(prev: dict[str, str], origin: str, destination: str) -> list[str]:
        if origin == destination:
            return [origin]
        path = [destination]
        while path[-1] != origin:
            path.append(prev[path[-1]])
        path.reverse()
        return path

    def _path_distance(self, path: list[str]) -> float:
        return sum(
            self.venue.distance(path[i], path[i + 1]) for i in range(len(path) - 1)
        )
