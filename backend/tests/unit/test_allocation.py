"""Unit tests for volunteer allocation."""

import pytest

from stadiummind.core.exceptions import OptimizationError
from stadiummind.optimization.allocation import allocate_volunteers


def test_empty_or_zero_returns_empty():
    assert allocate_volunteers({}, 10) == {}
    assert allocate_volunteers({"a": 1.0}, 0) == {}


def test_respects_total_pool():
    alloc = allocate_volunteers({"a": 5.0, "b": 3.0}, available=4, max_per_zone=6)
    assert sum(alloc.values()) <= 4


def test_prioritises_higher_weight():
    alloc = allocate_volunteers({"low": 1.0, "high": 9.0}, available=3, max_per_zone=3)
    # Highest weight zone should be served first.
    assert alloc.get("high", 0) >= alloc.get("low", 0)


def test_respects_max_per_zone():
    alloc = allocate_volunteers({"a": 5.0, "b": 4.0}, available=10, max_per_zone=2)
    assert all(v <= 2 for v in alloc.values())


def test_negative_available_raises():
    with pytest.raises(OptimizationError):
        allocate_volunteers({"a": 1.0}, available=-1)
