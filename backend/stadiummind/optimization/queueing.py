"""Queueing-theory estimates for service points (gates, tills, washrooms).

Implements the M/M/c (Erlang-C) model to estimate the expected waiting time
given an arrival rate, a per-server service rate and the number of parallel
servers. These are pure, side-effect-free functions and therefore ideal for
unit testing against known analytical values.
"""

from __future__ import annotations

import math

from stadiummind.core.exceptions import OptimizationError


def erlang_c(traffic_intensity: float, servers: int) -> float:
    """Probability that an arriving customer has to wait (Erlang-C formula).

    Parameters
    ----------
    traffic_intensity:
        Offered load ``a = lambda / mu`` (arrival rate over service rate).
    servers:
        Number of parallel servers ``c``.
    """
    if servers <= 0:
        raise OptimizationError("servers must be >= 1")
    a = max(0.0, traffic_intensity)
    rho = a / servers
    if rho >= 1.0:
        # System is unstable: an arriving customer effectively always waits.
        return 1.0

    # Sum of a^n / n! for n in [0, c-1].
    summation = sum(a**n / math.factorial(n) for n in range(servers))
    last_term = (a**servers / math.factorial(servers)) * (1.0 / (1.0 - rho))
    return last_term / (summation + last_term)


def expected_wait_minutes(
    arrival_rate_per_min: float,
    service_rate_per_min_per_server: float,
    servers: int,
) -> float:
    """Expected time a person waits in queue, in minutes (M/M/c).

    Returns a large sentinel (999.0) when the system is overloaded
    (``rho >= 1``) so callers can treat "unbounded" as "very bad" without
    special-casing infinities.
    """
    if service_rate_per_min_per_server <= 0:
        raise OptimizationError("service rate must be > 0")
    if servers <= 0:
        raise OptimizationError("servers must be >= 1")

    lam = max(0.0, arrival_rate_per_min)
    mu = service_rate_per_min_per_server
    a = lam / mu
    rho = a / servers
    if rho >= 1.0:
        return 999.0

    pw = erlang_c(a, servers)
    # Wq = C(c, a) / (c*mu - lambda)
    wq = pw / (servers * mu - lam)
    return max(0.0, wq)
