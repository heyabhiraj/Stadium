"""Volunteer / staff allocation as an optimisation problem.

Given a set of demand points (zones needing help, each with a weight) and a
pool of volunteers, decide how many volunteers to send to each zone to
maximise weighted coverage without exceeding the pool.

Two implementations share one signature:

* If ``pulp`` is installed, the problem is solved exactly as an integer linear
  program (ILP) — the "textbook" formulation.
* Otherwise a greedy fallback assigns volunteers to the highest-weight unmet
  demand first. For this particular problem (linear objective, single pool
  constraint) the greedy result matches the ILP optimum, so behaviour is
  consistent regardless of backend.
"""

from __future__ import annotations

import logging

from stadiummind.core.exceptions import OptimizationError

logger = logging.getLogger(__name__)


def allocate_volunteers(
    demands: dict[str, float],
    available: int,
    max_per_zone: int | None = None,
) -> dict[str, int]:
    """Allocate ``available`` volunteers across weighted ``demands``.

    Parameters
    ----------
    demands:
        Mapping of ``zone_id -> weight`` (higher weight == more urgent).
    available:
        Total number of volunteers to distribute (>= 0).
    max_per_zone:
        Optional cap on volunteers per zone. Defaults to ``available``.

    Returns
    -------
    dict
        Mapping of ``zone_id -> volunteers_assigned`` (zones with 0 omitted).
    """
    if available < 0:
        raise OptimizationError("available volunteers must be >= 0")
    if not demands or available == 0:
        return {}

    cap = max_per_zone if max_per_zone is not None else available
    if cap <= 0:
        raise OptimizationError("max_per_zone must be >= 1")

    try:
        return _allocate_ilp(demands, available, cap)
    except Exception:  # noqa: BLE001 - pulp missing or solver failure
        logger.info("volunteer allocation: falling back to greedy solver")
        return _allocate_greedy(demands, available, cap)


def _allocate_ilp(
    demands: dict[str, float], available: int, cap: int
) -> dict[str, int]:
    """Exact integer-linear-programming allocation via PuLP."""
    import pulp  # optional dependency

    problem = pulp.LpProblem("volunteer_allocation", pulp.LpMaximize)
    x = {
        zone: pulp.LpVariable(f"x_{zone}", lowBound=0, upBound=cap, cat="Integer")
        for zone in demands
    }
    # Objective: maximise total weighted coverage.
    problem += pulp.lpSum(weight * x[zone] for zone, weight in demands.items())
    # Constraint: do not exceed the available pool.
    problem += pulp.lpSum(x.values()) <= available
    problem.solve(pulp.PULP_CBC_CMD(msg=False))

    return {
        zone: int(round(var.value()))
        for zone, var in x.items()
        if var.value() and var.value() >= 1
    }


def _allocate_greedy(
    demands: dict[str, float], available: int, cap: int
) -> dict[str, int]:
    """Greedy allocation: fill highest-weight zones first up to the cap."""
    result: dict[str, int] = {}
    remaining = available
    # Highest weight first; stable order for determinism on ties.
    for zone, _weight in sorted(demands.items(), key=lambda kv: (-kv[1], kv[0])):
        if remaining <= 0:
            break
        take = min(cap, remaining)
        if take > 0:
            result[zone] = take
            remaining -= take
    return result
