"""Unit tests for queueing-theory helpers."""

import pytest

from stadiummind.core.exceptions import OptimizationError
from stadiummind.optimization.queueing import erlang_c, expected_wait_minutes


def test_erlang_c_bounds():
    # Very light load -> almost no waiting probability.
    assert 0.0 <= erlang_c(0.1, 4) < 0.05
    # Overloaded system -> always wait.
    assert erlang_c(10.0, 2) == 1.0


def test_expected_wait_low_load_is_small():
    # 20 arrivals/min, 8/min/server, 8 servers -> lightly loaded.
    wait = expected_wait_minutes(20, 8, 8)
    assert wait < 0.5


def test_expected_wait_increases_with_load():
    light = expected_wait_minutes(30, 8, 8)
    heavy = expected_wait_minutes(60, 8, 8)
    assert heavy > light


def test_overloaded_returns_sentinel():
    # Arrival rate exceeds total service capacity.
    assert expected_wait_minutes(100, 8, 8) == 999.0


def test_invalid_inputs_raise():
    with pytest.raises(OptimizationError):
        expected_wait_minutes(10, 0, 4)
    with pytest.raises(OptimizationError):
        expected_wait_minutes(10, 8, 0)
