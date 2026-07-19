"""Optional test for the SQLAlchemy repository.

Skipped automatically when SQLAlchemy is not installed. When it *is* installed
this exercises the real SQL persistence path end-to-end against an on-disk
SQLite database (an in-memory DB is avoided because each connection would get
its own empty schema), proving :class:`SqlRepository` is functional and not
just declarative.
"""

from __future__ import annotations

import pytest

pytest.importorskip("sqlalchemy")

from stadiummind.core.models import (  # noqa: E402
    Incident,
    IncidentType,
    Recommendation,
    Severity,
)
from stadiummind.infra.sql_repository import SqlRepository  # noqa: E402


@pytest.fixture
def repo(tmp_path):
    db_file = tmp_path / "test.db"
    return SqlRepository(f"sqlite:///{db_file}")


def test_incident_roundtrip_and_resolve(repo):
    inc = repo.save_incident(
        Incident.create(IncidentType.SECURITY, Severity.HIGH, "gate_1", "fight")
    )
    listed = repo.list_incidents(include_resolved=False)
    assert [i.id for i in listed] == [inc.id]

    repo.resolve_incident(inc.id)
    assert repo.list_incidents(include_resolved=False) == []
    all_incidents = repo.list_incidents(include_resolved=True)
    assert all_incidents[0].resolved is True
    # Enum round-trips correctly through the varchar column.
    assert all_incidents[0].type is IncidentType.SECURITY


def test_recommendation_upsert_and_decision(repo):
    rec = Recommendation.create("crowd", "Open Gate 5", "explanation", 0.9, zone_id="gate_5")
    repo.save_recommendation(rec)
    # Deterministic id => saving an equivalent recommendation upserts (no dup).
    repo.save_recommendation(
        Recommendation.create("crowd", "Open Gate 5", "explanation v2", 0.95, zone_id="gate_5")
    )
    assert len(repo.list_recommendations()) == 1

    updated = repo.set_recommendation_decision(rec.id, True)
    assert updated is not None and updated.approved is True
    assert repo.set_recommendation_decision("missing", False) is None
