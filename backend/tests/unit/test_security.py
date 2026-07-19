"""Unit tests for the demo auth token scheme."""

import time

import pytest

from stadiummind.core.config import Settings
from stadiummind.api.security import AuthError, issue_token, verify_token


def test_round_trip_token():
    s = Settings()
    token = issue_token(s, "alice", "operations")
    payload = verify_token(s, token)
    assert payload["sub"] == "alice"
    assert payload["role"] == "operations"


def test_unknown_role_rejected():
    s = Settings()
    with pytest.raises(AuthError):
        issue_token(s, "bob", "astronaut")


def test_tampered_token_rejected():
    s = Settings()
    token = issue_token(s, "alice", "fan")
    with pytest.raises(AuthError):
        verify_token(s, token + "x")


def test_expired_token_rejected():
    s = Settings(access_token_ttl_minutes=0)
    token = issue_token(s, "alice", "fan")
    time.sleep(0.01)
    with pytest.raises(AuthError):
        verify_token(s, token)


def test_wrong_secret_rejected():
    token = issue_token(Settings(jwt_secret="a"), "alice", "fan")
    with pytest.raises(AuthError):
        verify_token(Settings(jwt_secret="b"), token)
