"""Unit tests for security-related configuration and the production guard."""

import pytest

from stadiummind.core.config import Settings
from stadiummind.core.exceptions import ConfigurationError


def test_dev_config_is_permissive_but_safe():
    s = Settings()  # defaults = development
    assert s.is_production is False
    # In development the guard is a no-op.
    s.assert_production_safe()


def test_production_rejects_default_secret():
    s = Settings(environment="production")
    with pytest.raises(ConfigurationError) as exc:
        s.assert_production_safe()
    assert "JWT_SECRET" in str(exc.value)


def test_production_rejects_wildcard_cors():
    s = Settings(environment="production", jwt_secret="strong-secret",
                 allowed_origins=("*",))
    with pytest.raises(ConfigurationError) as exc:
        s.assert_production_safe()
    assert "CORS" in str(exc.value)


def test_production_rejects_disabled_rate_limit():
    s = Settings(environment="production", jwt_secret="strong-secret",
                 allowed_origins=("https://app.example",), rate_limit_per_minute=0)
    with pytest.raises(ConfigurationError):
        s.assert_production_safe()


def test_safe_production_config_passes():
    s = Settings(
        environment="production",
        jwt_secret="a-strong-unique-secret",
        allowed_origins=("https://stadiummind.example",),
        rate_limit_per_minute=240,
    )
    s.assert_production_safe()  # must not raise
    assert s.is_production is True
