"""Demo-grade authentication.

A deliberately small, dependency-free token scheme: a signed, base64 token
encodes the username, role and expiry using an HMAC of the configured secret.
It is *not* production hardened (no refresh, no revocation) but it demonstrates
the auth layer from the architecture and is easy to test.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time

from stadiummind.core.config import Settings
from stadiummind.core.exceptions import StadiumMindError


class AuthError(StadiumMindError):
    """Raised when a token is missing, malformed or expired."""


def issue_token(settings: Settings, username: str, role: str) -> str:
    """Create a signed access token for ``username`` with ``role``."""
    if role not in settings.roles:
        raise AuthError(f"unknown role {role!r}")
    payload = {
        "sub": username,
        "role": role,
        "exp": time.time() + settings.access_token_ttl_minutes * 60,
    }
    raw = json.dumps(payload, separators=(",", ":")).encode()
    body = base64.urlsafe_b64encode(raw).decode().rstrip("=")
    signature = _sign(settings, body)
    return f"{body}.{signature}"


def verify_token(settings: Settings, token: str) -> dict:
    """Validate a token and return its payload, or raise :class:`AuthError`."""
    try:
        body, signature = token.split(".", 1)
    except ValueError as exc:
        raise AuthError("malformed token") from exc

    if not hmac.compare_digest(signature, _sign(settings, body)):
        raise AuthError("bad signature")

    padded = body + "=" * (-len(body) % 4)
    payload = json.loads(base64.urlsafe_b64decode(padded))
    if payload.get("exp", 0) < time.time():
        raise AuthError("token expired")
    return payload


def _sign(settings: Settings, body: str) -> str:
    digest = hmac.new(settings.jwt_secret.encode(), body.encode(), hashlib.sha256)
    return base64.urlsafe_b64encode(digest.digest()).decode().rstrip("=")
